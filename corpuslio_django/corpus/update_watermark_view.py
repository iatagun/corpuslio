# Watermark Preference Update View

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def update_watermark_preference(request):
    """Update user's watermark preference via toggle in profile."""
    if request.method == 'POST':
        profile = request.user.profile
        enable_watermark = request.POST.get('enable_watermark') == 'on'
        
        profile.enable_watermark = enable_watermark
        profile.save()
        
        status = "aktif" if enable_watermark else "devre dışı"
        messages.success(request, f"Filigran tercihi {status} olarak kaydedildi.")
    
    return redirect('corpus:profile')
