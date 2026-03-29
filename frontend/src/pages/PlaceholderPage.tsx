interface PlaceholderPageProps {
  title: string;
  description: string;
}

export const PlaceholderPage = ({
  title,
  description,
}: PlaceholderPageProps) => {
  return (
    <div>
      <h2>{title}</h2>
      <p className="muted">{description}</p>
    </div>
  );
};
