"""Forms for document upload and processing."""

from django import forms
from .models import Document
from django.conf import settings


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    
    # Metadata fields
    author = forms.CharField(
        required=False,
        max_length=200,
        label="Yazar",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Orhan Pamuk'})
    )
    
    date = forms.CharField(
        required=False,
        max_length=50,
        label="Tarih/Yıl",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 2023 veya 19. Yüzyıl'})
    )
    
    source = forms.CharField(
        required=False,
        max_length=200,
        label="Kaynak",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Cumhuriyet Gazetesi'})
    )
    
    genre = forms.ChoiceField(
        required=False,
        label="Tür",
        choices=[
            ('', '-- Seçiniz --'),
            ('roman', 'Roman'),
            ('hikaye', 'Hikaye'),
            ('şiir', 'Şiir'),
            ('makale', 'Makale'),
            ('haber', 'Haber'),
            ('blog', 'Blog'),
            ('akademik', 'Akademik'),
            ('resmi', 'Resmi Belge'),
            ('diğer', 'Diğer'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    language = forms.CharField(
        required=False,
        initial='tr',
        max_length=10,
        label="Dil",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'tr'})
    )
    
    publisher = forms.CharField(
        required=False,
        max_length=200,
        label="Yayınevi",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: İletişim Yayınları'})
    )
    
    analyze = forms.BooleanField(
        required=False, 
        initial=True,
        label="Dilbilimsel Analiz Yap (POS/Lemma)",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    label_studio_export = forms.BooleanField(
        required=False,
        initial=False,
        label="Label Studio Formatında Kaydet",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = Document
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': ','.join(settings.ALLOWED_DOCUMENT_EXTENSIONS)
            })
        }
    
    def clean_file(self):
        """Validate file extension."""
        file = self.cleaned_data.get('file')
        if file:
            import os
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in settings.ALLOWED_DOCUMENT_EXTENSIONS:
                raise forms.ValidationError(
                    f'İzin verilen formatlar: {", ".join(settings.ALLOWED_DOCUMENT_EXTENSIONS)}'
                )
        return file
    
    def save(self, commit=True):
        """Save document with extracted filename, format, and metadata."""
        instance = super().save(commit=False)
        if instance.file:
            import os
            instance.filename = instance.file.name
            instance.format = os.path.splitext(instance.file.name)[1][1:].upper()
        
        # Save metadata
        instance.metadata = {
            'author': self.cleaned_data.get('author', ''),
            'date': self.cleaned_data.get('date', ''),
            'source': self.cleaned_data.get('source', ''),
            'genre': self.cleaned_data.get('genre', ''),
            'language': self.cleaned_data.get('language', 'tr'),
            'publisher': self.cleaned_data.get('publisher', ''),
        }
        
        if commit:
            instance.save()
        return instance

