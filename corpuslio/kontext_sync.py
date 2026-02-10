"""
OCRchestra → KonText Integration
Auto-sync workflow for corpus export
"""

import subprocess
import os
from pathlib import Path

class KonTextSync:
    def __init__(self, corpus_name="turkish_corpus"):
        self.corpus_name = corpus_name.upper().replace(" ", "_")
        self.wsl_data_dir = "/var/corpora/data"
        self.wsl_registry = "/var/corpora/registry"
        
    def export_to_kontext(self, vrt_content: str, corpus_id: str = None):
        """
        Export VRT to KonText via WSL2
        
        Args:
            vrt_content: VRT formatted string
            corpus_id: Optional corpus identifier
        """
        if corpus_id:
            self.corpus_name = corpus_id.upper().replace(" ", "_")
            
        # 1. Save VRT to temp file
        temp_vrt = f"temp_{self.corpus_name.lower()}.vrt"
        with open(temp_vrt, 'w', encoding='utf-8') as f:
            f.write(vrt_content)
        
        # 2. Convert Windows path to WSL path
        win_path = os.path.abspath(temp_vrt).replace('\\', '/')
        wsl_path = f"/mnt/c/{win_path[3:]}"  # C:\... -> /mnt/c/...
        
        # 3. Copy to WSL corpus directory
        vrt_dest = f"{self.wsl_data_dir}/{self.corpus_name.lower()}.vrt"
        cmd_copy = f'wsl cp "{wsl_path}" {vrt_dest}'
        subprocess.run(cmd_copy, shell=True, check=True)
        
        # 4. Encode with CWB
        corpus_dir = f"{self.wsl_data_dir}/{self.corpus_name.lower()}"
        registry_file = f"{self.wsl_registry}/{self.corpus_name.lower()}"
        
        cmd_encode = f'''wsl bash -c 'cwb-encode -d {corpus_dir} \\
            -f {vrt_dest} \\
            -R {registry_file} \\
            -c utf8 \\
            -P word -P lemma -P pos -P morph \\
            -S doc:0+id+filename+date \\
            -S p:0+id \\
            -S s:0+id' '''
        
        subprocess.run(cmd_encode, shell=True, check=True)
        
        # 5. Build indices
        cmd_index = f"wsl bash -c 'cwb-makeall -r {self.wsl_registry} {self.corpus_name}'"
        subprocess.run(cmd_index, shell=True, check=True)
        
        # 6. Clean up temp file
        os.remove(temp_vrt)
        
        return {
            'status': 'success',
            'corpus_name': self.corpus_name,
            'kontext_url': 'http://localhost:8080',
            'message': f'Corpus {self.corpus_name} indexed and ready in KonText'
        }
    
    def check_corpus_status(self):
        """Check if corpus exists in KonText"""
        cmd = f"wsl bash -c 'cwb-describe-corpus -r {self.wsl_registry} {self.corpus_name}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            return {
                'exists': True,
                'details': result.stdout
            }
        return {'exists': False}

# Usage in OCRchestra
if __name__ == "__main__":
    # Example: Export from OCRchestra
    from corpuslio.exporters import CorpusExporter
    
    # Get corpus data
    exporter = CorpusExporter(corpus_data, metadata)
    vrt_content = exporter.to_vrt(include_structure=True)
    
    # Sync to KonText
    sync = KonTextSync("my_corpus")
    result = sync.export_to_kontext(vrt_content)
    
    print(f"✅ {result['message']}")
    print(f"🔗 Access at: {result['kontext_url']}")
