export default function CarrierLink({ name, url }) {
  if (!name) {
    return null;
  }

  if (!url) {
    return <span>{name}</span>;
  }

  return (
    <a className="carrier-link" href={url} target="_blank" rel="noreferrer">
      {name}
    </a>
  );
}
