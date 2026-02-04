"""Forms for document upload and processing."""

from django import forms
from .models import Document
from django.conf import settings


class DocumentUploadForm(forms.ModelForm):
    """Form for uploading documents."""
    
    # Form Fields corresponding to Model Fields
    author = forms.CharField(
        required=False,
        label="Yazar",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Ömer Seyfettin'})
    )
    
    grade_level = forms.ChoiceField(
        required=False,
        label="Sınıf Seviyesi",
        choices=Document.GRADE_LEVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    subject = forms.CharField(
        required=False,
        label="Ders/Alan",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Türkçe, Matematik'})
    )
    
    publisher = forms.CharField(
        required=False,
        label="Yayınevi",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: MEB Yayınları'})
    )
    
    publication_year = forms.IntegerField(
        required=False,
        label="Basım Yılı",
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '2024'})
    )

    isbn = forms.CharField(
        required=False,
        label="ISBN",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '978-...'}),
    )
    
    source = forms.CharField(
        required=False,
        label="Kaynak Adı",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 5. Sınıf Türkçe Ders Kitabı'})
    )
    
    genre = forms.ChoiceField(
        required=False,
        label="Tür",
        choices=[
            ('', '-- Seçiniz --'),
            ('ders_kitabi', 'Ders Kitabı'),
            ('hikaye', 'Hikaye/Roman'),
            ('siir', 'Şiir'),
            ('makale', 'Makale'),
            ('soru_bankasi', 'Soru Bankası'),
            ('diger', 'Diğer'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
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
        fields = ['file', 'author', 'grade_level', 'subject', 'publisher', 'publication_year', 'isbn', 'source', 'genre']
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
        """Save document and auto-fill filename/format."""
        instance = super().save(commit=False)
        if instance.file:
            import os
            instance.filename = instance.file.name
            instance.format = os.path.splitext(instance.file.name)[1][1:].upper()
        
        # Metadata is now handled by model fields naturally via ModelForm
        
        if commit:
            instance.save()
        return instance

