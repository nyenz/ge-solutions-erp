// PATH: erp-frontend/scripts/midnight-map.mjs
// fix280: MIDNIGHT = GES DAY at night. It is made FROM the GES DAY skin (src/styles/gesday/src-*.css), rule for rule,
// so every page keeps the same layout, the same order of shades and the same accents (David: "MIDNIGHT must follow all
// the principles set by GES DAY"). Only the colours are turned for the dark:
//   backgrounds  light surfaces (white, cream, the grey third-shade card) become midnight shades, and the darker a
//                surface was in the day, the LIGHTER it is at night, so a card still stands off its panel; navy head
//                bands get deeper; the accents (tangerine, green, red, yellow, cyan buttons) stay as they are.
//   text         dark text (navy, grey, deep red, deep green) becomes light text of the same hue; light text stays.
//                Text on a solid accent button keeps its colour.
//   borders      dark hairlines become soft light hairlines.
//   shadows      stay dark (a white engraving shadow turns into a dark one).
// Used by scripts/build-gesday.mjs, which writes src/styles/midnight.css.

const COLOR = /#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b|rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*(?:,\s*[\d.]+\s*)?\)|\b(?:white|black)\b/g;

function parse(c) {
    const s = c.toLowerCase();
    if (s === 'white') return [255, 255, 255, 1];
    if (s === 'black') return [0, 0, 0, 1];
    if (s[0] === '#') {
        let h = s.slice(1);
        if (h.length <= 4) h = h.split('').map((x) => x + x).join('');
        const n = (i) => parseInt(h.slice(i, i + 2), 16);
        return [n(0), n(2), n(4), h.length === 8 ? n(6) / 255 : 1];
    }
    const p = s.replace(/rgba?\(|\)/g, '').split(',').map(Number);
    return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
}

function toHsl([r, g, b]) {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), min = Math.min(r, g, b), l = (max + min) / 2;
    let h = 0, s = 0;
    if (max !== min) {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        if (max === r) h = (g - b) / d + (g < b ? 6 : 0);
        else if (max === g) h = (b - r) / d + 2;
        else h = (r - g) / d + 4;
        h *= 60;
    }
    return [h, s, l];
}

function fromHsl(h, s, l) {
    const k = (n) => (n + h / 30) % 12;
    const a = s * Math.min(l, 1 - l);
    const f = (n) => l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));
    return [f(0), f(8), f(4)].map((v) => Math.round(Math.max(0, Math.min(1, v)) * 255));
}

function out([r, g, b], a) {
    if (a >= 0.999) return '#' + [r, g, b].map((v) => v.toString(16).padStart(2, '0')).join('').toUpperCase();
    return `rgba(${r},${g},${b},${+a.toFixed(3)})`;
}

/** an accent: a strong colour that is neither very light nor very dark (tangerine, green, red, yellow, cyan, blue) */
const isAccent = ([h, s, l]) => s > 0.5 && l > 0.3 && l < 0.72 && !(h >= 200 && h <= 240 && l < 0.45);
/** the GES navy family (head bands, navy text, navy hairlines) */
const isNavy = ([h, s, l]) => h >= 200 && h <= 240 && l < 0.45;

export function makeMapper(opts = {}) {
    const hue = opts.hue ?? 220;    // the hue of the night surfaces
    const sat = opts.sat ?? 0.42;   // how blue they are (0 = grey)
    const base = opts.base ?? 0.17; // the lightness of a surface that was white in the day

    const bg = (rgb, a) => {
        const hsl = toHsl(rgb);
        const [h, s, l] = hsl;
        if (l >= 0.6 && a < 0.6 && s < 0.3) return out(rgb, a);   // a see-through white wash (hover, glass) stays a wash
        if (l >= 0.6) {
            const nl = base + (1 - l) * 0.55;   // darker by day = lighter by night
            const warmOrGrey = s < 0.55 || (h >= 25 && h <= 65);
            return warmOrGrey ? out(fromHsl(hue, sat, nl), a) : out(fromHsl(h, Math.min(s, 0.5), nl), a);
        }
        if (isNavy(hsl)) return out(fromHsl(hue, Math.max(sat, Math.min(s, 0.7)), l * 0.62), a);   // head bands: deeper
        return out(rgb, a);   // accents and mid colours stay
    };
    const text = (rgb, a) => {
        const [h, s, l] = toHsl(rgb);
        if (l >= 0.5) return out(rgb, a);
        const navy = h >= 200 && h <= 240;
        return out(fromHsl(h, navy ? Math.min(s, 0.3) : Math.min(s, 0.8), 0.97 - l * 0.8), a);
    };
    const line = (rgb, a) => {
        const hsl = toHsl(rgb);
        if (hsl[2] >= 0.5 || isAccent(hsl)) return out(rgb, a);
        return out(fromHsl(hue, 0.45, 0.78), a);
    };
    const shade = (rgb, a) => (toHsl(rgb)[2] > 0.8 ? out([0, 0, 0], Math.min(1, a * 1.2)) : out(rgb, a));

    const ROLE = (prop) => {
        if (/^background/.test(prop)) return bg;
        if (/^(color|-webkit-text-fill-color|fill|stroke|caret-color|text-decoration-color|accent-color)$/.test(prop)) return text;
        if (/^(border|outline|column-rule)/.test(prop)) return line;
        if (/shadow$/.test(prop)) return shade;
        return null;
    };

    // selectors that sit on a solid accent (an orange tab, a green button): their text keeps its day colour
    const onAccent = new Set();
    const key = (sel) => sel.trim().replace(/\s+/g, ' ');   // exact selector: a hover colour does not count
    const learn = (rule) => {
        rule.walkDecls(/^background/, (d) => {
            const cs = d.value.match(COLOR) || [];
            if (cs.length && cs.every((c) => isAccent(toHsl(parse(c))))) rule.selectors.forEach((x) => onAccent.add(key(x)));
        });
    };

    /** turns one postcss rule (already a copy) into its night version */
    const apply = (rule) => {
        const accentBg = rule.selectors.some((x) => onAccent.has(key(x)));
        rule.walkDecls((d) => {
            const fn = ROLE(d.prop.toLowerCase());
            if (!fn) return;
            if (fn === text && accentBg) return;
            d.value = d.value.replace(COLOR, (c) => { const p = parse(c); return fn(p.slice(0, 3), p[3]); });
        });
    };
    return { learn, apply };
}
