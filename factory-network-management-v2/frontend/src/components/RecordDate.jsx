const formatter = new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Asia/Bangkok', year: 'numeric', month: '2-digit', day: '2-digit',
  hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
});

export default function RecordDate({ value }) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) return '—';
  const parts = Object.fromEntries(formatter.formatToParts(date).map(part => [part.type, part.value]));
  return <time dateTime={value} title="Asia/Bangkok (UTC+07:00)" className="whitespace-nowrap">{`${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}`}</time>;
}
