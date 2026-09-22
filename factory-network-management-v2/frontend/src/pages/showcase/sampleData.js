// Production Line Overview fixtures only. No API or business records.
export const sampleRows = [
  ['S27', 'bondi ag', 'Arista 7060 · LYB · LB9', 10, 'WORKING'],
  ['W17', 'bondi ag', 'Arista 7050 · Arista 7060', 8, 'WORKING'],
  ['V17', 'bondi ag', 'LYB · T1048', 6, 'NOT WORKING'],
  ['C20', 'assembly area', 'Arista 7060 · LYB · LB9', 12, 'WORKING'],
  ['S17', 'assembly area', 'Arista 7050 · Arista 7060', 9, 'WORKING'],
  ['A01', 'packing area', 'LYB · T1048', 4, 'NOT WORKING'],
  ['B02', 'packing area', 'Arista 7060 · LYB · LB9', 7, 'WORKING'],
  ['D03', 'test area', 'Arista 7050 · Arista 7060', 11, 'NOT WORKING'],
  ['E04', 'test area', 'LYB · T1048', 5, 'WORKING'],
  ['F05', 'assembly area', 'Arista 7060 · LYB · LB9', 14, 'WORKING'],
  ['G06', 'packing area', 'Arista 7050 · Arista 7060', 3, 'NOT WORKING'],
  ['H07', 'test area', 'LYB · T1048', 8, 'WORKING'],
  ['J08', 'assembly area', 'Arista 7060 · LYB · LB9', 16, 'WORKING'],
  ['K09', 'packing area', 'Arista 7050 · Arista 7060', 6, 'NOT WORKING'],
  ['L10', 'test area', 'LYB · T1048', 2, 'NOT WORKING'],
].map(([name, supportingInfo, vendor, total, status]) => ({ id: `demo-line-${name}`, name, supportingInfo, model_names: name === 'S27' ? ['S8Z PDB', 'S8Z'] : [], vendor, total, status }));
