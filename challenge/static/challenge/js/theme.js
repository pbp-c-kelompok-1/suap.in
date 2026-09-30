// Mode terang / gelap
import { $ } from './utils.js';

function setTheme(t) {
  document.documentElement.dataset.theme = t;
  $('#themeIco').setAttribute('href', t === 'dark' ? '#i-sun' : '#i-moon');
}
$('#themeBtn').addEventListener('click', () => {
  const cur = document.documentElement.dataset.theme || 'light';
  setTheme(cur === 'dark' ? 'light' : 'dark');
});
setTheme('light');
