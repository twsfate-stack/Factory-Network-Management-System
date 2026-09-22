import { useState } from 'react';
import { mediaUrl } from '../services/api';

export default function CatalogImage({ url, name, compact = false }) {
  const [failed, setFailed] = useState(null);
  return <div className={compact ? 'catalog-image catalog-image-thumb' : 'catalog-image'}>
    {url && failed !== url ? <img src={mediaUrl(url)} alt={`${name} switch model`} onError={() => setFailed(url)} />
      : <span className="muted" aria-label="No switch model image">{compact ? '\u2014' : 'No image'}</span>}
  </div>;
}
