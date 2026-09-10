// Production Line Overview fixtures only. No API or business records.
export const sampleRows = [
  ['S27', 'bondi ag', 'Arista 7060 · LYB · LB9', 10, 'Active'],
  ['W17', 'bondi ag', 'Arista 7050 · Arista 7060', 8, 'Active'],
  ['V17', 'bondi ag', 'LYB · T1048', 6, 'Offline'],
  ['C20', 'assembly area', 'Arista 7060 · LYB · LB9', 12, 'Active'],
  ['S17', 'assembly area', 'Arista 7050 · Arista 7060', 9, 'Active'],
  ['A01', 'packing area', 'LYB · T1048', 4, 'Spare'],
  ['B02', 'packing area', 'Arista 7060 · LYB · LB9', 7, 'Active'],
  ['D03', 'test area', 'Arista 7050 · Arista 7060', 11, 'Offline'],
  ['E04', 'test area', 'LYB · T1048', 5, 'Active'],
  ['F05', 'assembly area', 'Arista 7060 · LYB · LB9', 14, 'Active'],
  ['G06', 'packing area', 'Arista 7050 · Arista 7060', 3, 'Spare'],
  ['H07', 'test area', 'LYB · T1048', 8, 'Active'],
  ['J08', 'assembly area', 'Arista 7060 · LYB · LB9', 16, 'Active'],
  ['K09', 'packing area', 'Arista 7050 · Arista 7060', 6, 'Offline'],
  ['L10', 'test area', 'LYB · T1048', 2, 'Spare'],
].map(([name, supportingInfo, vendor, total, status]) => ({ id: `demo-line-${name}`, name, supportingInfo, vendor, total, status }));
