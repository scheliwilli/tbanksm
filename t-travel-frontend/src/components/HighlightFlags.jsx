export default function HighlightFlags({ isCheapest, isFastest, className = '' }) {
  if (!isCheapest && !isFastest) {
    return null;
  }

  const classes = ['highlight-flags', className].filter(Boolean).join(' ');

  return (
    <div className={classes}>
      {isCheapest && <span className="flight-flag flight-flag--cheap">Самый дешевый</span>}
      {isFastest && <span className="flight-flag flight-flag--fast">Самый быстрый</span>}
    </div>
  );
}
