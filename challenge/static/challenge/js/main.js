// Entry point: dipanggil dari template lewat <script type="module">
import { $ } from './utils.js';
import { initSubTabs, renderCond, renderPubProfile } from './reference.js';
import { mountMascots } from './mascot.js';
import { renderChest, renderQuests } from './misi.js';
import { renderNotifs } from './notifikasi.js';
import { renderProfile } from './profil.js';
import { renderRank, renderReport } from './laporan.js';
import { route } from './router.js';
import './theme.js';

mountMascots();
$('#mascotLand').appendChild($('#mascot-tpl').content.cloneNode(true));
$('#avoBig').appendChild($('#mascot-tpl').content.cloneNode(true));
initSubTabs('#page-auth', '#authTabs');
initSubTabs('#page-scanner', '#scanTabs');
renderPubProfile('me');
renderCond('sehat');
renderQuests(); renderChest(); renderReport(); renderRank(); renderNotifs(); renderProfile();
if (!location.hash) location.hash = '#/misi';
route();
