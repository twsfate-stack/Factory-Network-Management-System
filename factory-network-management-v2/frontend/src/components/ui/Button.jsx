export default function Button({ variant = 'primary', className = '', type = 'button', ...props }) {
  return <button type={type} className={`button button-${variant} ${className}`} {...props} />;
}
