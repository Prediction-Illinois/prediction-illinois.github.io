// Preview typography studies without saving a browser preference.
const logoDirections = new Set(['industrial', 'editorial', 'wordmark']);
const requestedLogo = new URLSearchParams(location.search).get('logo');
if (logoDirections.has(requestedLogo)) document.documentElement.dataset.logo = requestedLogo;

const frame = document.querySelector('.hero-frame');
if (frame) {
const images = [...document.querySelectorAll('.market-image')];
const buttons = [...document.querySelectorAll('.market-tab')];
const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
let current = 0;
let inView = true;
let timer;
let selection = 0;
const activate = async (index) => {
  const request = ++selection;
  const next = images[index];
  if (!next.hasAttribute('src')) next.src = next.dataset.src;
  try { await next.decode(); } catch { return; }
  if (request !== selection) return;
  current = index;
  images.forEach((image, i) => {
    image.classList.toggle('is-active', i === index);
    image.setAttribute('aria-hidden', String(i !== index));
  });
  buttons.forEach((button, i) => {
    button.classList.toggle('is-active', i === index);
    button.setAttribute('aria-pressed', String(i === index));
  });
};
const syncReel = () => {
  clearInterval(timer);
  if (!motionPreference.matches && inView && !document.hidden) timer = setInterval(() => activate((current + 1) % images.length), 6500);
};
buttons.forEach((button, index) => button.addEventListener('click', () => {
  activate(index);
  syncReel();
}));
motionPreference.addEventListener('change', syncReel);
document.addEventListener('visibilitychange', syncReel);
if ('IntersectionObserver' in window) new IntersectionObserver(([entry]) => { inView = entry.isIntersecting; syncReel(); }).observe(frame);
else syncReel();

}
