from huggingface_hub import snapshot_download
import os
snapshot_download("tiiuae/falcon-7b-instruct", local_dir="models/falcon-7b-instruct")