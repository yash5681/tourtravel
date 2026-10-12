document.addEventListener('DOMContentLoaded', () => {
  const menu = document.getElementById('menuBtn'), nav = document.getElementById('nav');
  if (menu) menu.addEventListener('click', () => nav.classList.toggle('open'));

  const lightbox = document.getElementById('lightbox'), lbImg = document.getElementById('lightboxImg');
  if (lightbox) {
    document.querySelectorAll('.gallery img').forEach(img =>
      img.addEventListener('click', () => {
        lbImg.src = img.src;
        lightbox.classList.add('open');
      })
    );
    document.getElementById('closeLightbox').onclick = () => lightbox.classList.remove('open');
    lightbox.onclick = e => { if (e.target === lightbox) lightbox.classList.remove('open'); };
  }
});
