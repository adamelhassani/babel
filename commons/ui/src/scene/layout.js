export function mulberry(a) {
  return function () {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export function boatTarget(i, round, n) {
  const rnd = mulberry(i * 7919 + round * 104729 + 13);
  const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n + (rnd() - 0.5) * 0.3;
  const rad = 1.0 + rnd() * 0.07;
  return {ang, rad};
}
