// Data avatar: 10 karakter x 10 warna + avatar spesial makanan/minuman

/* ---------------- AVATAR SYSTEM: 10 karakter x 10 warna = 100 ---------------- */
export const SPECIES = [
  { n: 'Tunas', lv: 1 }, { n: 'Jamur', lv: 1 }, { n: 'Kaktus', lv: 3 }, { n: 'Awan', lv: 5 }, { n: 'Tetes Air', lv: 8 },
  { n: 'Bunga', lv: 10 }, { n: 'Kura-kura', lv: 15 }, { n: 'Lebah', lv: 20 }, { n: 'Bumi', lv: 30 }, { n: 'Pohon', lv: 40 },
];
export const PAL = [
  { n: 'Lime',   a: '#00E676', b: '#0A9F62', c: '#C7FFE3' },
  { n: 'Teal',   a: '#0DA69B', b: '#086866', c: '#C0F5F2' },
  { n: 'Biru',   a: '#4B90FF', b: '#1A4FA0', c: '#CFE3FF' },
  { n: 'Hijau',  a: '#35C06A', b: '#126C36', c: '#C8F5D9' },
  { n: 'Madu',   a: '#F5A623', b: '#B87400', c: '#FFE9B3' },
  { n: 'Koral',  a: '#FF7A7A', b: '#C23B3B', c: '#FFD3D3' },
  { n: 'Ungu',   a: '#9B7BFF', b: '#6248C9', c: '#E1D6FF' },
  { n: 'Permen', a: '#FF8FB8', b: '#D6478A', c: '#FFD6E7' },
  { n: 'Laut',   a: '#4DD8CE', b: '#0A8880', c: '#D2FAF6' },
  { n: 'Batu',   a: '#AEB8B7', b: '#5E6B66', c: '#E8EDEC' },
];
const K = '#12201D';
const L = 'stroke-linecap="round" stroke-linejoin="round"';
export const cheeks = `<ellipse cx="-23" cy="7" rx="5" ry="3.2" fill="#FF7A7A" opacity=".45"/><ellipse cx="23" cy="7" rx="5" ry="3.2" fill="#FF7A7A" opacity=".45"/>`;
const eyeOval = `<g class="blink"><ellipse cx="-13" cy="-2" rx="3.8" ry="5.2" fill="${K}"/><ellipse cx="13" cy="-2" rx="3.8" ry="5.2" fill="${K}"/><circle cx="-12" cy="-4" r="1.5" fill="#fff"/><circle cx="14" cy="-4" r="1.5" fill="#fff"/></g>`;
export const FACE = [
  /*0 senyum manis*/ eyeOval + `<path d="M-6 8q6 6 12 0" stroke="${K}" stroke-width="2.8" fill="none" ${L}/>`,
  /*1 ketawa*/ `<g class="blink"><path d="M-18 0q5-7 10 0M8 0q5-7 10 0" stroke="${K}" stroke-width="3" fill="none" ${L}/></g><path d="M-7 6h14q0 10-7 10t-7-10z" fill="${K}"/><path d="M-3.5 13q3.5-3 7 0q-3.5 3-7 0z" fill="#FF7A7A"/>`,
  /*2 dot + w*/ `<g class="blink"><circle cx="-13" cy="-2" r="3.4" fill="${K}"/><circle cx="13" cy="-2" r="3.4" fill="${K}"/></g><path d="M-8 7q4 5 8 0q4 5 8 0" stroke="${K}" stroke-width="2.6" fill="none" ${L}/>`,
  /*3 ngantuk*/ `<g class="blink"><path d="M-18 -1h10M8 -1h10" stroke="${K}" stroke-width="3.2" fill="none" ${L}/></g><path d="M-4 9q4 3 8 0" stroke="${K}" stroke-width="2.6" fill="none" ${L}/>`,
  /*4 berbinar*/ `<g class="blink"><ellipse cx="-13" cy="-2" rx="5.2" ry="6.4" fill="${K}"/><ellipse cx="13" cy="-2" rx="5.2" ry="6.4" fill="${K}"/><circle cx="-11" cy="-5" r="2.2" fill="#fff"/><circle cx="15" cy="-5" r="2.2" fill="#fff"/><circle cx="-14.5" cy="0" r="1.1" fill="#fff"/><circle cx="11.5" cy="0" r="1.1" fill="#fff"/></g><path d="M-7 8q7 7 14 0" stroke="${K}" stroke-width="2.8" fill="none" ${L}/>`,
  /*5 kedip*/ `<path d="M-18 -1q5-6 10 0" stroke="${K}" stroke-width="3" fill="none" ${L}/><circle cx="13" cy="-2" r="3.6" fill="${K}"/><path d="M-6 7h12q0 9-6 9t-6-9z" fill="${K}"/><ellipse cx="0" cy="13.4" rx="3.6" ry="2.4" fill="#FF7A7A"/>`,
  /*6 kaget*/ `<g class="blink"><circle cx="-13" cy="-2" r="6" fill="#fff"/><circle cx="13" cy="-2" r="6" fill="#fff"/><circle cx="-12" cy="-1" r="3" fill="${K}"/><circle cx="14" cy="-1" r="3" fill="${K}"/></g><ellipse cx="0" cy="11" rx="3.2" ry="4.2" fill="${K}"/>`,
  /*7 ><*/ `<path d="M-19 -6l8 4l-8 4M19 -6l-8 4l8 4" stroke="${K}" stroke-width="3" fill="none" ${L}/><path d="M-7 7h14a7 7 0 0 1-14 0z" fill="${K}"/>`,
  /*8 kacamata*/ `<circle cx="-13" cy="-2" r="8" fill="#fff" fill-opacity=".7" stroke="${K}" stroke-width="2.4"/><circle cx="13" cy="-2" r="8" fill="#fff" fill-opacity=".7" stroke="${K}" stroke-width="2.4"/><path d="M-5 -2h10" stroke="${K}" stroke-width="2.4"/><g class="blink"><circle cx="-12" cy="-1" r="2.6" fill="${K}"/><circle cx="14" cy="-1" r="2.6" fill="${K}"/></g><path d="M-6 11q6 5 12 0" stroke="${K}" stroke-width="2.6" fill="none" ${L}/>`,
  /*9 semangat*/ eyeOval + `<path d="M-20 -12l12 4M20 -12l-12 4" stroke="${K}" stroke-width="3" fill="none" ${L}/><path d="M-8 7q8 9 16 0z" fill="${K}"/>`,
];
const hl = (x, y, rx = 9, ry = 5, r = -28) => `<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" transform="rotate(${r} ${x} ${y})" fill="#fff" opacity=".4"/>`;
export const BODY = [
  /*0 Tunas*/ p => ({ x: 60, y: 76, s: 1, svg:
    `<path d="M60 30c-2-14-14-20-28-18 0 14 9 22 28 18Z" fill="#35C06A"/><path d="M60 30c2-12 14-18 28-16-1 14-10 22-28 16Z" fill="#1EA854"/>
     <path d="M60 28c22 0 38 17 38 42 0 25-15 42-38 42S22 95 22 70c0-25 16-42 38-42Z" fill="${p.a}"/>
     <path d="M26 84c5 17 20 26 40 24-26 8-46-6-40-24Z" fill="${p.b}" opacity=".3"/>${hl(42, 48)}` }),
  /*1 Jamur*/ p => ({ x: 60, y: 96, s: .72, svg:
    `<path d="M40 72h40v24c0 10-9 16-20 16s-20-6-20-16Z" fill="${p.c}"/>
     <path d="M10 76C10 44 33 22 60 22s50 22 50 54Z" fill="${p.a}"/>
     <path d="M10 76h100v3c0 4-4 7-8 7H18c-4 0-8-3-8-7Z" fill="${p.b}" opacity=".4"/>
     <circle cx="34" cy="54" r="7" fill="#fff" opacity=".85"/><circle cx="64" cy="40" r="5.5" fill="#fff" opacity=".85"/><circle cx="88" cy="58" r="7.5" fill="#fff" opacity=".85"/><circle cx="58" cy="62" r="4" fill="#fff" opacity=".85"/>` }),
  /*2 Kaktus*/ p => ({ x: 60, y: 66, s: .95, svg:
    `<path d="M26 62v22q0 8 8 8h12M94 54v24q0 8-8 8H74" stroke="${p.a}" stroke-width="13" fill="none" ${L}/>
     <rect x="38" y="20" width="44" height="92" rx="22" fill="${p.a}"/>
     <rect x="45" y="34" width="5" height="52" rx="2.5" fill="#fff" opacity=".28"/>
     <path d="M40 100c4 10 12 12 20 12s16-2 20-12z" fill="${p.b}" opacity=".25"/>
     <circle cx="60" cy="16" r="7" fill="#FF8FB8"/><circle cx="53" cy="20" r="5" fill="#FF8FB8"/><circle cx="67" cy="20" r="5" fill="#FF8FB8"/><circle cx="60" cy="19" r="3.4" fill="#FFD36B"/>` }),
  /*3 Awan*/ p => ({ x: 62, y: 72, s: .95, svg:
    `<g fill="${p.a}"><circle cx="36" cy="72" r="22"/><circle cx="62" cy="54" r="28"/><circle cx="88" cy="74" r="20"/><rect x="30" y="70" width="66" height="28" rx="14"/></g>
     <path d="M34 92h58q-4 6-12 6H46q-8 0-12-6Z" fill="${p.b}" opacity=".22"/>${hl(50, 38, 10, 5, -30)}
     <path d="M46 103q4 6 0 9q-4-3 0-9M76 104q4 6 0 9q-4-3 0-9" fill="#74ACFF"/>` }),
  /*4 Tetes*/ p => ({ x: 60, y: 84, s: .95, svg:
    `<path d="M60 8C60 8 22 52 22 78c0 21 17 35 38 35s38-14 38-35C98 52 60 8 60 8Z" fill="${p.a}"/>
     <path d="M28 90c4 14 18 22 34 22-22 6-42-6-34-22Z" fill="${p.b}" opacity=".3"/>
     <path d="M36 74c0-9 4-17 11-24" stroke="#fff" stroke-width="6" fill="none" opacity=".5" ${L}/>` }),
  /*5 Bunga*/ p => {
    let pet = ''; for (let k = 0; k < 8; k++) { const a = k * Math.PI / 4; pet += `<circle cx="${(60 + 31 * Math.cos(a)).toFixed(1)}" cy="${(54 + 31 * Math.sin(a)).toFixed(1)}" r="16" fill="${p.a}"/>`; }
    return { x: 60, y: 54, s: .8, svg:
    `<rect x="56" y="84" width="8" height="30" rx="4" fill="#1EA854"/><path d="M62 104c10-10 22-8 28-2-8 8-20 8-28 2Z" fill="#35C06A"/>${pet}<circle cx="60" cy="54" r="27" fill="${p.c}"/>` }; },
  /*6 Kura*/ p => ({ x: 60, y: 93, s: .82, svg:
    `<ellipse cx="30" cy="106" rx="13" ry="8" fill="${p.b}"/><ellipse cx="90" cy="106" rx="13" ry="8" fill="${p.b}"/>
     <path d="M20 78h80v14c0 14-17 22-40 22S20 106 20 92Z" fill="${p.a}"/>
     <path d="M12 80C12 46 32 24 60 24s48 22 48 56Z" fill="${p.b}"/>
     <circle cx="60" cy="42" r="10" fill="${p.a}" opacity=".55"/><circle cx="34" cy="60" r="8" fill="${p.a}" opacity=".55"/><circle cx="86" cy="60" r="8" fill="${p.a}" opacity=".55"/>` }),
  /*7 Lebah*/ p => ({ x: 60, y: 62, s: .92, svg:
    `<ellipse cx="36" cy="32" rx="17" ry="11" transform="rotate(-25 36 32)" fill="#fff" opacity=".85"/><ellipse cx="84" cy="32" rx="17" ry="11" transform="rotate(25 84 32)" fill="#fff" opacity=".85"/>
     <path d="M50 28q-6-14-14-16M70 28q6-14 14-16" stroke="${K}" stroke-width="3" fill="none" ${L}/><circle cx="36" cy="11" r="3.6" fill="${K}"/><circle cx="84" cy="11" r="3.6" fill="${K}"/>
     <ellipse cx="60" cy="72" rx="42" ry="40" fill="${p.a}"/>
     <path d="M22 90q38 20 76 0" stroke="${p.b}" stroke-width="9" fill="none" ${L}/><path d="M32 103q28 12 56 0" stroke="${p.b}" stroke-width="8" fill="none" ${L}/>${hl(38, 50)}` }),
  /*8 Bumi*/ p => ({ x: 60, y: 66, s: 1, svg:
    `<circle cx="60" cy="62" r="47" fill="${p.a}"/>
     <path d="M26 40c8-9 21-11 27-4 4 6-4 10-2 16s-12 9-21 5-10-11-4-17Z" fill="${p.c}" opacity=".6"/>
     <path d="M86 68c9 0 13 9 9 17s-17 11-21 5 2-22 12-22Z" fill="${p.c}" opacity=".6"/>
     <path d="M40 100c12 8 30 8 42-2" stroke="${p.b}" stroke-width="5" fill="none" opacity=".3" ${L}/>${hl(38, 34, 9, 5, -35)}` }),
  /*9 Pohon*/ p => ({ x: 60, y: 88, s: .8, svg:
    `<rect x="50" y="94" width="20" height="20" rx="6" fill="#8A5A2B"/>
     <path d="M60 50 106 102H14Z" fill="${p.a}" stroke="${p.a}" stroke-width="6" stroke-linejoin="round"/>
     <path d="M60 28 100 76H20Z" fill="${p.a}" stroke="${p.a}" stroke-width="6" stroke-linejoin="round"/><path d="M60 28 100 76H20Z" fill="${p.b}" opacity=".3"/>
     <path d="M60 6 92 46H28Z" fill="${p.c}" stroke="${p.c}" stroke-width="6" stroke-linejoin="round"/>` }),
];
/* ---------------- AVATAR SPESIAL: makanan & minuman khas Indonesia ---------------- */
export const SPECIALS = [
  { n: 'Nasi Goreng', lv: 2, f: 4, d: 'Sarapan sejuta umat. Telur ceplok di atas, semangat di dalam.', draw: () => ({ x: 60, y: 72, s: .82, svg:
    `<ellipse cx="60" cy="98" rx="52" ry="14" fill="#fff" stroke="#E4E9E8" stroke-width="3"/>
     <path d="M16 94Q20 44 60 42Q100 44 104 94Q60 108 16 94Z" fill="#E8A75A"/>
     <path d="M30 90q0-30 20-38" stroke="#fff" stroke-width="5" fill="none" opacity=".3" ${L}/>
     <g fill="#A85B1C" opacity=".55"><circle cx="28" cy="82" r="2.4"/><circle cx="94" cy="74" r="2.4"/><circle cx="86" cy="92" r="2.4"/><circle cx="34" cy="66" r="2.2"/><circle cx="99" cy="88" r="2"/></g>
     <circle cx="42" cy="34" r="12" fill="#fff"/><circle cx="78" cy="34" r="12" fill="#fff"/><ellipse cx="60" cy="32" rx="26" ry="14" fill="#fff"/>
     <circle cx="60" cy="30" r="9" fill="#FFC83D"/><circle cx="57" cy="27" r="2.6" fill="#fff" opacity=".7"/>
     <circle cx="97" cy="99" r="8" fill="#63D68C"/><circle cx="97" cy="99" r="4.5" fill="#C8F5D9"/><circle cx="21" cy="101" r="8" fill="#EB4848"/><path d="M21 93q3-4 6-2" stroke="#1EA854" stroke-width="2.5" fill="none" ${L}/>` }) },
  { n: 'Tempe', lv: 4, f: 0, d: 'Protein nabati asli Indonesia. Jejak karbonnya jauh lebih ringan dari daging.', draw: () => ({ x: 60, y: 66, s: .85, svg:
    `<rect x="18" y="24" width="84" height="82" rx="20" fill="#DCC98E" stroke="#B89F5F" stroke-width="3"/>
     <g fill="#8F7A3E" opacity=".55"><circle cx="30" cy="38" r="3"/><circle cx="50" cy="32" r="2.6"/><circle cx="74" cy="34" r="3"/><circle cx="92" cy="44" r="2.6"/><circle cx="27" cy="58" r="2.6"/><circle cx="94" cy="62" r="3"/><circle cx="26" cy="76" r="2.6"/><circle cx="95" cy="78" r="2.6"/></g>
     <path d="M16 92Q60 82 104 92V104Q60 114 16 104Z" fill="#35C06A"/><path d="M20 99Q60 90 100 99" stroke="#126C36" stroke-width="2.5" fill="none" opacity=".5" ${L}/>
     ${hl(34, 40, 10, 4, -20)}` }) },
  { n: 'Es Teh Manis', lv: 6, f: 9, d: 'Segar, manis, dan selalu ada di warteg.', draw: () => ({ x: 60, y: 74, s: .72, svg:
    `<path d="M32 22H88L82 106Q60 114 38 106Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M34.6 40H85.4L81 104Q60 111 39 104Z" fill="#D98A2B"/>
     <rect x="40" y="38" width="16" height="16" rx="4" fill="#fff" opacity=".5" transform="rotate(-10 48 46)"/><rect x="62" y="40" width="16" height="16" rx="4" fill="#fff" opacity=".45" transform="rotate(12 70 48)"/>
     <path d="M68 4L60 50" stroke="#EB4848" stroke-width="6" ${L}/><path d="M66.6 14L64.6 26" stroke="#fff" stroke-width="6" ${L}/>
     <circle cx="90" cy="26" r="13" fill="#FFE066"/><circle cx="90" cy="26" r="9" fill="#FFF3A8"/><path d="M90 17v18M81 26h18M83.5 19.5l13 13M96.5 19.5l-13 13" stroke="#F5C42A" stroke-width="1.6" ${L}/>
     <path d="M40 58v34" stroke="#fff" stroke-width="4" opacity=".35" ${L}/>` }) },
  { n: 'Bakso', lv: 8, f: 2, d: 'Bulat, hangat, dan paling enak pas hujan.', draw: () => ({ x: 60, y: 52, s: .95, svg:
    `<ellipse cx="60" cy="70" rx="50" ry="11" fill="#F5A623" opacity=".55"/>
     <circle cx="28" cy="62" r="15" fill="#C99C6E"/><circle cx="92" cy="62" r="15" fill="#C99C6E"/><circle cx="60" cy="50" r="33" fill="#D8B48C"/>
     <ellipse cx="44" cy="30" rx="8" ry="4.5" transform="rotate(-30 44 30)" fill="#fff" opacity=".4"/>
     <g fill="#1EA854"><circle cx="24" cy="76" r="2.4"/><circle cx="50" cy="82" r="2.4"/><circle cx="76" cy="81" r="2.4"/><circle cx="98" cy="75" r="2.4"/></g>
     <path d="M10 70Q60 92 110 70L104 84Q98 112 60 114Q22 112 16 84Z" fill="#fff" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M13 79Q60 100 107 79" stroke="#2F80ED" stroke-width="5" fill="none" ${L}/>` }) },
  { n: 'Sate', lv: 11, f: 1, d: 'Tusuk demi tusuk, dibakar sampai wangi.', draw: () => ({ x: 60, y: 67, s: .7, svg:
    `<path d="M60 3V117" stroke="#D9B26A" stroke-width="6" ${L}/>
     <rect x="24" y="16" width="72" height="30" rx="14" fill="#B35A2B"/><rect x="20" y="50" width="80" height="34" rx="16" fill="#C06A33"/><rect x="24" y="88" width="72" height="28" rx="13" fill="#B35A2B"/>
     <g stroke="#7A3A18" stroke-width="3" opacity=".55" ${L}><path d="M34 26v10M86 26v10M32 98v10M88 98v10"/></g>
     <path d="M34 22h22M30 56h18M34 94h20" stroke="#fff" stroke-width="3.5" opacity=".25" ${L}/>` }) },
  { n: 'Klepon', lv: 13, f: 5, d: 'Gigit, lalu meletus manis gula merah.', draw: () => {
    let f = ''; for (let k = 0; k < 18; k++) { const a = k * 2.4, r = 26 + (k % 3) * 6, cx = 60 + r * Math.cos(a), cy = 66 + r * Math.sin(a); f += `<rect x="${(cx - 4).toFixed(1)}" y="${(cy - 2).toFixed(1)}" width="8" height="4" rx="2" fill="#fff" opacity=".92" transform="rotate(${(k * 47) % 180} ${cx.toFixed(1)} ${cy.toFixed(1)})"/>`; }
    return { x: 60, y: 68, s: .95, svg: `<circle cx="60" cy="66" r="42" fill="#63D68C" stroke="#35C06A" stroke-width="3"/>${f}${hl(40, 42, 10, 5, -35)}` }; } },
  { n: 'Onde-onde', lv: 15, f: 6, d: 'Renyah wijen di luar, kacang hijau di dalam.', draw: () => {
    let f = ''; for (let k = 0; k < 26; k++) { const a = k * 2.399, r = 6 + (k * 13 % 34), cx = 60 + r * Math.cos(a), cy = 66 + r * Math.sin(a); f += `<ellipse cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" rx="3.2" ry="1.8" fill="#FFF3D0" transform="rotate(${(k * 53) % 180} ${cx.toFixed(1)} ${cy.toFixed(1)})"/>`; }
    return { x: 60, y: 68, s: .95, svg: `<circle cx="60" cy="66" r="42" fill="#F2B233" stroke="#D9931A" stroke-width="3"/>${f}` }; } },
  { n: 'Es Cendol', lv: 18, f: 0, d: 'Hijau kenyal, santan, dan gula aren.', draw: () => ({ x: 60, y: 46, s: .66, svg:
    `<path d="M32 22H88L82 106Q60 114 38 106Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M32.6 30H87.4L85.1 62H34.9Z" fill="#FFF6E0"/><path d="M34.9 62H85.1L83.4 86H36.6Z" fill="#8A4B1E"/><path d="M36.6 86H83.4L81.9 106Q60 113 38.1 106Z" fill="#63D68C"/>
     <path d="M42 94q4-6 8 0t8 0t8 0t8 0M44 101q4-6 8 0t8 0t8 0t8 0" stroke="#1EA854" stroke-width="3.5" fill="none" ${L}/>
     <path d="M80 4L76 48" stroke="#FF8FB8" stroke-width="6" ${L}/>` }) },
  { n: 'Martabak', lv: 22, f: 9, d: 'Tebal, manis, dan cocok dimakan ramai-ramai.', draw: () => ({ x: 60, y: 76, s: .78, svg:
    `<path d="M12 92A48 48 0 0 1 108 92Z" fill="#F5A623" stroke="#D98A1A" stroke-width="3" stroke-linejoin="round"/>
     <path d="M28 62q8-9 16 0t16 0t16 0t16 0" stroke="#5B2B12" stroke-width="5" fill="none" ${L}/>
     <g fill="#FFE58A"><circle cx="46" cy="52" r="3.5"/><circle cx="74" cy="50" r="3.5"/><circle cx="34" cy="74" r="3.5"/><circle cx="88" cy="72" r="3.5"/></g>
     <path d="M12 92h96v8q-48 14-96 0Z" fill="#C77C00"/><path d="M14 98q46 12 92 0" stroke="#F5C24B" stroke-width="2.4" fill="none" opacity=".7" ${L}/>` }) },
  { n: 'Kopi Susu', lv: 25, f: 3, d: 'Teman begadang tugas kuliah.', draw: () => ({ x: 52, y: 82, s: .78, svg:
    `<path d="M42 30q-6-10 0-18M58 30q-6-10 0-18M74 30q-6-10 0-18" stroke="#AEB8B7" stroke-width="4" fill="none" ${L}/>
     <ellipse cx="54" cy="111" rx="44" ry="7" fill="#E4E9E8"/>
     <path d="M90 50h5a12 12 0 0 1 0 24h-6" stroke="#CFE3FF" stroke-width="13" fill="none" ${L}/><path d="M90 50h5a12 12 0 0 1 0 24h-6" stroke="#fff" stroke-width="7" fill="none" ${L}/>
     <path d="M16 42H92V78Q92 110 54 110Q16 110 16 78Z" fill="#fff" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <ellipse cx="54" cy="42" rx="38" ry="9" fill="#F3DFC1" stroke="#CFE3FF" stroke-width="3"/><ellipse cx="54" cy="43" rx="31" ry="6.5" fill="#7A4523"/>
     <path d="M18 60H90" stroke="#2F80ED" stroke-width="5"/>` }) },
  { n: 'Es Kelapa Muda', lv: 30, f: 1, d: 'Segar alami, langsung dari buahnya.', draw: () => ({ x: 60, y: 80, s: .88, svg:
    `<path d="M60 28C94 28 106 54 104 80C102 102 84 112 60 112C36 112 18 102 16 80C14 54 26 28 60 28Z" fill="#A8E0A0" stroke="#5FBF72" stroke-width="3"/>
     <path d="M30 60Q28 84 40 100M92 58Q96 84 84 102" stroke="#5FBF72" stroke-width="3" fill="none" opacity=".5" ${L}/>
     <ellipse cx="60" cy="34" rx="28" ry="10" fill="#fff"/><ellipse cx="60" cy="34" rx="22" ry="7" fill="#CFF6F2"/>
     <path d="M72 3L64 36" stroke="#FF8FB8" stroke-width="6" ${L}/>` }) },
  { n: 'Tumpeng', lv: 35, f: 4, d: 'Avatar legendaris untuk perayaan besar.', draw: () => ({ x: 60, y: 68, s: .8, svg:
    `<ellipse cx="60" cy="104" rx="52" ry="10" fill="#1EA854"/><ellipse cx="60" cy="102" rx="52" ry="9" fill="#35C06A"/>
     <path d="M60 14L98 102H22Z" fill="#FFC83D" stroke="#F2B233" stroke-width="5" stroke-linejoin="round"/>
     <path d="M50 44L34 90" stroke="#fff" stroke-width="5" opacity=".35" ${L}/>
     <path d="M60 4c7 5 8 12 3 19-7-3-9-12-3-19Z" fill="#EB4848"/><path d="M60 6q-1-4 2-6" stroke="#1EA854" stroke-width="2.4" fill="none" ${L}/>
     <g><circle cx="28" cy="100" r="6" fill="#63D68C"/><circle cx="44" cy="104" r="6" fill="#F5A623"/><circle cx="76" cy="104" r="6" fill="#EB4848"/><circle cx="92" cy="100" r="6" fill="#63D68C"/></g>` }) },
  { n: 'Pisang Goreng', lv: 3, f: 4, d: 'Renyah di luar, hangat di dalam. Gorengan wajib sore hari.', draw: () => ({ x: 58, y: 76, s: .85, svg:
    `<ellipse cx="74" cy="44" rx="34" ry="16" transform="rotate(-22 74 44)" fill="#E39A1F"/>
     <path d="M12 76c0-22 16-38 46-38s46 16 46 38-16 32-46 32-46-10-46-32Z" fill="#F5C24B" stroke="#D98A1A" stroke-width="3"/>
     <g fill="#E39A1F" opacity=".5"><circle cx="26" cy="72" r="4"/><circle cx="96" cy="68" r="5"/><circle cx="34" cy="96" r="3.4"/><circle cx="88" cy="94" r="4"/><circle cx="50" cy="48" r="3"/><circle cx="76" cy="46" r="3.6"/></g>
     ${hl(34, 54, 10, 4, -25)}` }) },
  { n: 'Jamu', lv: 5, f: 0, d: 'Kunyit asam penjaga semangat, andalan si mbok.', draw: () => ({ x: 60, y: 84, s: .68, svg:
    `<path d="M70 26c8-8 18-4 20 3-8 5-17 4-20-3Z" fill="#35C06A"/>
     <rect x="46" y="10" width="28" height="14" rx="5" fill="#B87C4B"/><rect x="50" y="22" width="20" height="26" rx="4" fill="#fff" fill-opacity=".6" stroke="#CFE3FF" stroke-width="3"/>
     <rect x="30" y="42" width="60" height="70" rx="20" fill="#F5A623" stroke="#D98A1A" stroke-width="3"/>
     <rect x="30" y="66" width="60" height="34" fill="#FFF6E0"/><path d="M30 66H90M30 100H90" stroke="#D98A1A" stroke-width="2" opacity=".5"/>
     <path d="M38 50v10" stroke="#fff" stroke-width="4" opacity=".5" ${L}/>` }) },
  { n: 'Kerupuk', lv: 7, f: 6, d: 'Kriuk pelengkap segala hidangan.', draw: () => {
    let o = '', c = ''; for (let k = 0; k < 14; k++) { const a = k * Math.PI * 2 / 14, x = (60 + 34 * Math.cos(a)).toFixed(1), y = (66 + 34 * Math.sin(a)).toFixed(1); o += `<circle cx="${x}" cy="${y}" r="12" fill="#EBB27A"/>`; c += `<circle cx="${x}" cy="${y}" r="10.5" fill="#FFD9AE"/>`; }
    return { x: 60, y: 68, s: .95, svg: `${o}${c}<circle cx="60" cy="66" r="38" fill="#FFD9AE"/><g fill="#EBB27A" opacity=".55"><circle cx="30" cy="52" r="2.4"/><circle cx="92" cy="50" r="2.8"/><circle cx="28" cy="84" r="2.6"/><circle cx="94" cy="86" r="2.4"/><circle cx="60" cy="30" r="2.4"/><circle cx="62" cy="102" r="2.6"/></g>` }; } },
  { n: 'Soto Ayam', lv: 10, f: 1, d: 'Kuah kuning hangat, obat segala lapar.', draw: () => ({ x: 60, y: 90, s: .78, svg:
    `<path d="M26 22q-6-10 0-18M60 22q-6-10 0-18M94 22q-6-10 0-18" stroke="#AEB8B7" stroke-width="4" fill="none" ${L}/>
     <path d="M10 58Q14 110 60 112Q106 110 110 58Z" fill="#fff" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M13 72Q60 88 107 72" stroke="#2F80ED" stroke-width="5" fill="none" ${L}/>
     <ellipse cx="60" cy="58" rx="50" ry="13" fill="#fff" stroke="#CFE3FF" stroke-width="3"/><ellipse cx="60" cy="58" rx="43" ry="10" fill="#FFD54A"/>
     <ellipse cx="38" cy="56" rx="12" ry="7" fill="#fff"/><circle cx="38" cy="55" r="4.4" fill="#FFC83D"/>
     <path d="M64 55q6-3 12 0M72 60q6-2 10 1" stroke="#F3DDB3" stroke-width="4" fill="none" ${L}/>
     <g fill="#1EA854"><circle cx="54" cy="61" r="2.4"/><circle cx="86" cy="57" r="2.4"/><circle cx="50" cy="54" r="2.2"/><circle cx="92" cy="61" r="2.2"/></g>` }) },
  { n: 'Wedang Jahe', lv: 12, f: 9, d: 'Hangat di tenggorokan, hangat di hati.', draw: () => ({ x: 54, y: 78, s: .74, svg:
    `<path d="M38 30q-6-10 0-18M56 30q-6-10 0-18M74 30q-6-10 0-18" stroke="#AEB8B7" stroke-width="4" fill="none" ${L}/>
     <path d="M86 52h6a12 12 0 0 1 0 26h-6" stroke="#CFE3FF" stroke-width="13" fill="none" ${L}/><path d="M86 52h6a12 12 0 0 1 0 26h-6" stroke="#fff" stroke-width="7" fill="none" ${L}/>
     <path d="M18 38H90V100Q90 112 78 112H30Q18 112 18 100Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M21 46H87V99Q87 108 77 108H31Q21 108 21 99Z" fill="#E8973A"/>
     <path d="M28 52v40" stroke="#fff" stroke-width="4" opacity=".35" ${L}/>
     <path d="M96 100c6-6 16-2 14 6s-12 10-18 5-2-8 4-11Z" fill="#E3B97A" stroke="#C08F4F" stroke-width="2.5"/><path d="M98 104q5 0 8 3" stroke="#C08F4F" stroke-width="2" fill="none" ${L}/>` }) },
  { n: 'Gado-gado', lv: 16, f: 2, d: 'Sayur segar disiram saus kacang. Nabati dan mengenyangkan.', draw: () => ({ x: 60, y: 84, s: .78, svg:
    `<ellipse cx="60" cy="100" rx="54" ry="13" fill="#fff" stroke="#E4E9E8" stroke-width="3"/>
     <path d="M16 98Q18 42 60 40Q102 42 104 98Q60 110 16 98Z" fill="#63D68C"/>
     <path d="M20 64Q22 24 60 22Q98 24 100 64Q92 58 86 68Q78 56 70 68Q62 56 54 68Q46 56 38 68Q30 56 20 64Z" fill="#A8642B"/>
     <ellipse cx="44" cy="36" rx="8" ry="3.6" transform="rotate(-20 44 36)" fill="#fff" opacity=".3"/>
     <circle cx="22" cy="98" r="8" fill="#EB4848"/><path d="M22 90q3-4 6-2" stroke="#1EA854" stroke-width="2.5" fill="none" ${L}/>
     <rect x="88" y="90" width="14" height="14" rx="3" fill="#F3DFA5" stroke="#D9C27A" stroke-width="2"/>
     <ellipse cx="100" cy="76" rx="10" ry="7" fill="#fff" stroke="#E4E9E8" stroke-width="2"/><circle cx="100" cy="76" r="3.6" fill="#FFC83D"/>` }) },
  { n: 'Es Campur', lv: 20, f: 4, d: 'Segalanya campur jadi satu, dan justru itu serunya.', draw: () => ({ x: 60, y: 78, s: .78, svg:
    `<ellipse cx="60" cy="113" rx="26" ry="4" fill="#CFE3FF"/><rect x="54" y="100" width="12" height="12" fill="#CFE3FF"/>
     <path d="M14 46H106Q106 100 60 104Q14 100 14 46Z" fill="#FF9BB8" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M16 58H104" stroke="#fff" stroke-width="4" opacity=".65" ${L}/>
     <path d="M18 48Q22 16 60 14Q98 16 102 48Z" fill="#EAF7FF" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <rect x="30" y="28" width="14" height="14" rx="3" fill="#63D68C" transform="rotate(-12 37 35)"/><rect x="54" y="18" width="14" height="14" rx="3" fill="#EB4848" transform="rotate(10 61 25)"/><rect x="76" y="32" width="14" height="14" rx="3" fill="#FFD54A" transform="rotate(-8 83 39)"/>
     <path d="M40 46q6-6 12 0t12 0t12 0" stroke="#FF9BB8" stroke-width="3.5" fill="none" ${L}/>` }) },
  { n: 'Rendang', lv: 40, f: 9, d: 'Dimasak berjam-jam sampai bumbunya meresap. Sabar itu enak.', draw: () => ({ x: 60, y: 64, s: .85, svg:
    `<ellipse cx="60" cy="100" rx="54" ry="13" fill="#fff" stroke="#E4E9E8" stroke-width="3"/>
     <g fill="#B3592E"><circle cx="36" cy="66" r="22"/><circle cx="84" cy="66" r="22"/><circle cx="60" cy="50" r="28"/><circle cx="60" cy="76" r="26"/></g>
     <path d="M30 84q10 14 30 14t30-14" stroke="#8A3B1E" stroke-width="6" fill="none" opacity=".5" ${L}/>
     <path d="M40 38q8-6 16-4M70 34q10 0 14 6M24 58q2-8 8-10" stroke="#E0A06A" stroke-width="4" fill="none" opacity=".55" ${L}/>
     <g fill="#E8C48A" opacity=".9"><circle cx="30" cy="80" r="2.2"/><circle cx="92" cy="78" r="2.2"/><circle cx="52" cy="92" r="2.2"/><circle cx="78" cy="90" r="2.2"/></g>
     <circle cx="22" cy="98" r="6" fill="#EB4848"/><circle cx="22" cy="98" r="2.6" fill="#FFD3D3"/><path d="M84 100c8-10 20-8 26-2-8 8-18 8-26 2Z" fill="#35C06A"/>` }) },
  { n: 'Mie Ayam', lv: 9, f: 1, d: 'Mi kenyal, ayam manis gurih, langganan makan siang anak kos.', draw: () => ({ x: 60, y: 90, s: .78, svg:
    `<path d="M10 58Q14 110 60 112Q106 110 110 58Z" fill="#fff" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M13 74Q60 90 107 74" stroke="#EB4848" stroke-width="5" fill="none" ${L}/>
     <ellipse cx="60" cy="58" rx="50" ry="13" fill="#fff" stroke="#CFE3FF" stroke-width="3"/>
     <ellipse cx="60" cy="52" rx="42" ry="14" fill="#FFD54A"/>
     <path d="M24 50q8-9 16 0t16 0t16 0t16 0M28 57q8-8 16 0t16 0t16 0t12 0" stroke="#F2B233" stroke-width="4" fill="none" ${L}/>
     <circle cx="44" cy="44" r="6" fill="#B3592E"/><circle cx="72" cy="42" r="6.4" fill="#B3592E"/><circle cx="86" cy="52" r="5" fill="#B3592E"/>
     <g fill="#1EA854"><circle cx="58" cy="48" r="2.4"/><circle cx="30" cy="54" r="2.4"/><circle cx="92" cy="58" r="2.2"/><circle cx="64" cy="58" r="2.2"/></g>` }) },
  { n: 'Bubur Ayam', lv: 14, f: 0, d: 'Sarapan lembut yang bikin pagi terasa ramah.', draw: () => ({ x: 60, y: 50, s: .72, svg:
    `<path d="M16 68Q16 22 60 20Q104 22 104 68Z" fill="#FFF6E0" stroke="#EAD9B8" stroke-width="3" stroke-linejoin="round"/>
     <path d="M30 34q10-8 22-2M70 30q12-4 20 6" stroke="#F5A623" stroke-width="4" fill="none" ${L}/>
     <path d="M24 46q4-6 10-6" stroke="#E0A06A" stroke-width="4" fill="none" ${L}/>
     <circle cx="88" cy="32" r="9" fill="#FFD9AE" stroke="#EBB27A" stroke-width="2"/><rect x="18" y="24" width="8" height="26" rx="4" transform="rotate(-24 22 37)" fill="#D98A2B"/>
     <g fill="#1EA854"><circle cx="46" cy="28" r="2.4"/><circle cx="76" cy="26" r="2.4"/><circle cx="98" cy="50" r="2.2"/></g>
     <rect x="8" y="62" width="104" height="9" rx="4.5" fill="#086866"/><path d="M10 71H110Q108 112 60 113Q12 112 10 71Z" fill="#0DA69B"/>
     <path d="M22 80q0 14 12 20" stroke="#fff" stroke-width="4" fill="none" opacity=".4" ${L}/>` }) },
  { n: 'Ayam Geprek', lv: 17, f: 7, d: 'Digeprek, disambal, siap bikin keringetan.', draw: () => ({ x: 46, y: 64, s: .8, svg:
    `<path d="M74 82L100 106" stroke="#E4D2B0" stroke-width="15" ${L}/><path d="M74 82L100 106" stroke="#FFF6E0" stroke-width="9" ${L}/>
     <circle cx="106" cy="102" r="7" fill="#FFF6E0" stroke="#E4D2B0" stroke-width="2.5"/><circle cx="98" cy="111" r="7" fill="#FFF6E0" stroke="#E4D2B0" stroke-width="2.5"/>
     <path d="M12 62C12 28 42 12 72 20C98 28 102 58 84 76C68 92 40 98 26 84C18 76 12 70 12 62Z" fill="#EFA93A" stroke="#C77C00" stroke-width="3"/>
     <g fill="#C77C00" opacity=".45"><circle cx="24" cy="50" r="3.4"/><circle cx="88" cy="46" r="3.4"/><circle cx="76" cy="80" r="3"/><circle cx="30" cy="82" r="3"/></g>
     <path d="M42 22q12-8 26 2q10 10-4 14q-14 2-24-4q-6-6 2-12Z" fill="#EB4848"/><g fill="#FFD3D3"><circle cx="52" cy="28" r="1.8"/><circle cx="62" cy="26" r="1.8"/><circle cx="66" cy="34" r="1.8"/></g>` }) },
  { n: 'Pempek', lv: 19, f: 5, d: 'Ikan dan sagu, dicocol cuko asam pedas.', draw: () => ({ x: 46, y: 70, s: .85, svg:
    `<ellipse cx="50" cy="66" rx="44" ry="34" fill="#E9B96E" stroke="#C9903F" stroke-width="3"/>
     <g fill="#C9903F" opacity=".5"><circle cx="20" cy="58" r="3"/><circle cx="34" cy="94" r="3"/><circle cx="70" cy="92" r="3"/><circle cx="82" cy="60" r="3.4"/><circle cx="30" cy="44" r="2.6"/></g>
     <ellipse cx="72" cy="42" rx="13" ry="8" fill="#fff" stroke="#E4D2B0" stroke-width="2"/><circle cx="72" cy="42" r="4.6" fill="#FFC83D"/>
     <path d="M78 94H112Q110 114 95 114Q80 114 78 94Z" fill="#5B2B12"/><ellipse cx="95" cy="94" rx="17" ry="4.5" fill="#3E1D0A"/><ellipse cx="95" cy="93.5" rx="13" ry="2.8" fill="#7A3A18"/>` }) },
  { n: 'Lemper', lv: 21, f: 3, d: 'Ketan gurih berisi suwiran ayam, dibungkus daun pisang.', draw: () => ({ x: 54, y: 68, s: .8, svg:
    `<rect x="10" y="38" width="90" height="58" rx="29" fill="#35C06A" stroke="#1EA854" stroke-width="3"/>
     <path d="M22 46H90M16 56H96M16 80H96M22 90H90" stroke="#1EA854" stroke-width="2" opacity=".45" ${L}/>
     <ellipse cx="100" cy="67" rx="12" ry="24" fill="#FFF6E0" stroke="#E4D2B0" stroke-width="3"/><ellipse cx="102" cy="67" rx="6" ry="14" fill="#F3E4C3"/>` }) },
  { n: 'Kolak', lv: 24, f: 2, d: 'Manis hangat untuk menutup hari, apalagi saat berbuka.', draw: () => ({ x: 60, y: 90, s: .78, svg:
    `<path d="M10 58Q14 110 60 112Q106 110 110 58Z" fill="#fff" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M13 74Q60 90 107 74" stroke="#1EA854" stroke-width="5" fill="none" ${L}/>
     <ellipse cx="60" cy="58" rx="50" ry="13" fill="#fff" stroke="#CFE3FF" stroke-width="3"/><ellipse cx="60" cy="58" rx="43" ry="10" fill="#B86B2E"/>
     <ellipse cx="38" cy="57" rx="8" ry="4.6" fill="#FFE9A8"/><ellipse cx="56" cy="61" rx="8" ry="4.4" fill="#FFE9A8"/><ellipse cx="80" cy="56" rx="8" ry="4.6" fill="#FFE9A8"/>
     <rect x="62" y="52" width="10" height="8" rx="2" fill="#F5A623"/><rect x="88" y="58" width="9" height="7" rx="2" fill="#F5A623"/>
     <path d="M44 52q6-6 12-2" stroke="#35C06A" stroke-width="3.5" fill="none" ${L}/>` }) },
  { n: 'Dadar Gulung', lv: 27, f: 4, d: 'Gulungan hijau berisi kelapa manis.', draw: () => ({ x: 52, y: 78, s: .8, svg:
    `<rect x="22" y="24" width="74" height="34" rx="17" transform="rotate(-8 58 41)" fill="#4FCB7E" stroke="#35C06A" stroke-width="3"/>
     <rect x="10" y="52" width="86" height="52" rx="26" fill="#63D68C" stroke="#35C06A" stroke-width="3"/>
     <ellipse cx="96" cy="78" rx="12" ry="26" fill="#8A5A2B" stroke="#6E4520" stroke-width="2.5"/><path d="M96 66a6 6 0 1 1-2 10a9 9 0 0 0 3 9" stroke="#D9B26A" stroke-width="3" fill="none" ${L}/>` }) },
  { n: 'Es Alpukat', lv: 32, f: 6, d: 'Lembut, creamy, dan cokelatnya jangan pelit.', draw: () => ({ x: 60, y: 76, s: .72, svg:
    `<path d="M32 22H88L82 106Q60 114 38 106Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M34.6 40H85.4L81 104Q60 111 39 104Z" fill="#B7DE72"/>
     <path d="M33 28H87L85.8 42Q60 52 34.2 42Z" fill="#5B2B12"/><path d="M42 44q-2 10 2 16M78 44q3 8-1 18" stroke="#5B2B12" stroke-width="4" fill="none" ${L}/>
     <path d="M74 4L66 44" stroke="#FF8FB8" stroke-width="6" ${L}/><path d="M40 68v24" stroke="#fff" stroke-width="4" opacity=".35" ${L}/>` }) },
  { n: 'Kue Lapis', lv: 38, f: 9, d: 'Dikupas lapis demi lapis, kesabaran yang manis.', draw: () => ({ x: 60, y: 66, s: .8, svg:
    `<rect x="16" y="26" width="88" height="80" rx="18" fill="#FF8FB8"/>
     <rect x="16" y="42" width="88" height="11" fill="#fff" opacity=".85"/><rect x="16" y="62" width="88" height="11" fill="#fff" opacity=".85"/><rect x="16" y="82" width="88" height="10" fill="#fff" opacity=".85"/>
     <rect x="16" y="26" width="88" height="80" rx="18" fill="none" stroke="#D6478A" stroke-width="3"/>` }) },
  { n: 'Ketupat', lv: 45, f: 4, d: 'Simbol kebersamaan yang dianyam dengan sabar.', draw: () => ({ x: 60, y: 68, s: .78, svg:
    `<path d="M60 22q-6-10-14-8M60 22q6-10 14-8" stroke="#35C06A" stroke-width="4" fill="none" ${L}/>
     <g transform="rotate(45 60 66)"><rect x="28" y="34" width="64" height="64" rx="12" fill="#63D68C" stroke="#35C06A" stroke-width="3"/>
     <path d="M44 34V98M60 34V98M76 34V98M28 50H92M28 66H92M28 82H92" stroke="#35C06A" stroke-width="3" opacity=".7"/></g>
     <circle cx="60" cy="68" r="27" fill="#C8F5D9" opacity=".9"/>` }) },
  { n: 'Es Doger', lv: 6, f: 4, d: 'Warna-warni segar, favorit sore hari di pinggir jalan.', draw: () => ({ x: 60, y: 76, s: .72, svg:
    `<path d="M32 22H88L82 106Q60 114 38 106Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M34.6 40H85.4L81 104Q60 111 39 104Z" fill="#FF9BB8"/>
     <circle cx="46" cy="54" r="6" fill="#FFD54A"/><circle cx="62" cy="60" r="5" fill="#63D68C"/><circle cx="74" cy="50" r="5.4" fill="#FFF3D0"/><circle cx="54" cy="72" r="4.4" fill="#F5A623"/>
     <path d="M78 4L70 42" stroke="#EB4848" stroke-width="6" ${L}/>` }) },
  { n: 'Kue Cubit', lv: 8, f: 9, d: 'Kecil, empuk, dan toping meses berwarna-warni.', draw: () => ({ x: 60, y: 74, s: .84, svg:
    `<circle cx="30" cy="86" r="20" fill="#F5D98A" stroke="#D9B85C" stroke-width="3"/><circle cx="90" cy="86" r="20" fill="#F5D98A" stroke="#D9B85C" stroke-width="3"/>
     <circle cx="60" cy="66" r="42" fill="#FFE7A8" stroke="#D9B85C" stroke-width="3"/>
     <g fill="#2F80ED"><rect x="42" y="44" width="4" height="4"/><rect x="56" y="40" width="4" height="4"/><rect x="70" y="46" width="4" height="4"/></g>
     <g fill="#EB4848"><rect x="48" y="52" width="4" height="4"/><rect x="66" y="54" width="4" height="4"/><rect x="76" y="42" width="4" height="4"/></g>` }) },
  { n: 'Bandrek', lv: 15, f: 3, d: 'Rempah hangat dari tanah Sunda, penghalau dingin.', draw: () => ({ x: 54, y: 80, s: .74, svg:
    `<path d="M40 28q-6-10 0-18M58 28q-6-10 0-18" stroke="#AEB8B7" stroke-width="4" fill="none" ${L}/>
     <path d="M86 50h6a12 12 0 0 1 0 26h-6" stroke="#CFE3FF" stroke-width="13" fill="none" ${L}/><path d="M86 50h6a12 12 0 0 1 0 26h-6" stroke="#fff" stroke-width="7" fill="none" ${L}/>
     <path d="M18 36H90V98Q90 110 78 110H30Q18 110 18 98Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M21 44H87V97Q87 106 77 106H31Q21 106 21 97Z" fill="#8A5228"/>
     <path d="M50 20c6-6 14-2 14 4-6 4-12 2-14-4Z" fill="#35C06A"/><path d="M28 58v36" stroke="#fff" stroke-width="4" opacity=".3" ${L}/>` }) },
  { n: 'Kue Putu', lv: 23, f: 6, d: 'Berisi gula merah cair, berbalut kelapa parut.', draw: () => {
    let c = ''; for (let k = 0; k < 20; k++) { const a = k * 2.4, r = 6 + (k * 11 % 32), cx = 60 + r * Math.cos(a), cy = 68 + r * Math.sin(a); c += `<ellipse cx="${cx.toFixed(1)}" cy="${cy.toFixed(1)}" rx="3" ry="1.7" fill="#fff" transform="rotate(${(k * 41) % 180} ${cx.toFixed(1)} ${cy.toFixed(1)})"/>`; }
    return { x: 60, y: 70, s: .85, svg: `<rect x="24" y="30" width="72" height="76" rx="30" fill="#63D68C" stroke="#35C06A" stroke-width="3"/>${c}<circle cx="60" cy="70" r="9" fill="#B3592E"/>` }; } },
  { n: 'Es Pisang Ijo', lv: 26, f: 0, d: 'Pisang berbalut adonan hijau, disiram sirup merah.', draw: () => ({ x: 60, y: 74, s: .72, svg:
    `<path d="M32 22H88L82 106Q60 114 38 106Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M34.6 40H85.4L81 104Q60 111 39 104Z" fill="#EAF7F1"/><rect x="46" y="52" width="28" height="46" rx="14" fill="#63D68C"/>
     <path d="M80 4L72 42" stroke="#EB4848" stroke-width="6" ${L}/><path d="M78.6 14L76.6 26" stroke="#fff" stroke-width="6" ${L}/>` }) },
  { n: 'Serabi', lv: 28, f: 4, d: 'Gurih santan dengan siraman gula merah cair.', draw: () => ({ x: 60, y: 72, s: .88, svg:
    `<ellipse cx="60" cy="90" rx="52" ry="10" fill="#B3592E" opacity=".4"/>
     <circle cx="60" cy="66" r="46" fill="#FFF6E0" stroke="#EAD9B8" stroke-width="3"/>
     <path d="M60 30v72M32 42q28 8 56 0M26 66q34 10 68 0M32 90q28 8 56 0" stroke="#EAD9B8" stroke-width="2" opacity=".6" fill="none"/>
     <path d="M40 66c8 4 32 4 40 0-4 10-36 10-40 0Z" fill="#B3592E"/>` }) },
  { n: 'Kacang Rebus', lv: 29, f: 1, d: 'Camilan sederhana sambil ngobrol santai.', draw: () => ({ x: 60, y: 68, s: .82, svg:
    `<ellipse cx="60" cy="106" rx="46" ry="9" fill="#C9903F" opacity=".35"/>
     <path d="M28 30C10 34 8 60 24 68 12 78 16 104 40 106 46 92 44 70 34 58 44 48 42 34 28 30Z" fill="#7FBF6A" stroke="#4E9A3E" stroke-width="3"/>
     <path d="M92 30C110 34 112 60 96 68 108 78 104 104 80 106 74 92 76 70 86 58 76 48 78 34 92 30Z" fill="#7FBF6A" stroke="#4E9A3E" stroke-width="3"/>
     <path d="M34 58h52" stroke="#4E9A3E" stroke-width="3" opacity=".5"/>` }) },
  { n: 'Bir Pletok', lv: 33, f: 5, d: 'Merah rempah khas Betawi, hangat tanpa alkohol.', draw: () => ({ x: 54, y: 78, s: .72, svg:
    `<path d="M40 30q-6-10 0-18M58 30q-6-10 0-18" stroke="#AEB8B7" stroke-width="4" fill="none" ${L}/>
     <path d="M18 36H90V98Q90 110 78 110H30Q18 110 18 98Z" fill="#fff" fill-opacity=".55" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M21 44H87V97Q87 106 77 106H31Q21 106 21 97Z" fill="#D9384B"/>
     <circle cx="70" cy="60" r="4" fill="#FFD9AE" opacity=".8"/><circle cx="40" cy="78" r="3.4" fill="#FFD9AE" opacity=".8"/><path d="M28 58v36" stroke="#fff" stroke-width="4" opacity=".3" ${L}/>` }) },
  { n: 'Kue Putri Salju', lv: 36, f: 8, d: 'Renyah bertabur gula halus, favorit musim lebaran.', draw: () => ({ x: 60, y: 72, s: .86, svg:
    `<path d="M60 26 92 84H28Z" fill="#F2D9A0" stroke="#D9B85C" stroke-width="3" stroke-linejoin="round"/>
     <g fill="#fff" opacity=".95"><circle cx="40" cy="56" r="2.6"/><circle cx="56" cy="40" r="2.6"/><circle cx="72" cy="58" r="2.6"/><circle cx="50" cy="70" r="2.6"/><circle cx="70" cy="74" r="2.6"/><circle cx="60" cy="58" r="2.6"/><circle cx="34" cy="70" r="2.2"/><circle cx="82" cy="68" r="2.2"/></g>` }) },
  { n: 'Wedang Ronde', lv: 42, f: 6, d: 'Bola ketan kenyal dalam kuah jahe hangat.', draw: () => ({ x: 60, y: 88, s: .76, svg:
    `<path d="M42 26q-6-10 0-18M60 26q-6-10 0-18M78 26q-6-10 0-18" stroke="#AEB8B7" stroke-width="4" fill="none" ${L}/>
     <path d="M12 56Q16 108 60 110Q104 108 108 56Z" fill="#fff" stroke="#CFE3FF" stroke-width="3" stroke-linejoin="round"/>
     <path d="M15 70Q60 86 105 70" stroke="#D98A2B" stroke-width="5" fill="none" ${L}/>
     <ellipse cx="60" cy="56" rx="48" ry="12" fill="#fff" stroke="#CFE3FF" stroke-width="3"/><ellipse cx="60" cy="56" rx="41" ry="9" fill="#E8973A"/>
     <circle cx="42" cy="55" r="7" fill="#fff"/><circle cx="60" cy="58" r="6.5" fill="#EB4848"/><circle cx="78" cy="54" r="6.5" fill="#fff"/>` }) },
];
SPECIALS.sort((a, b) => a.lv - b.lv);
