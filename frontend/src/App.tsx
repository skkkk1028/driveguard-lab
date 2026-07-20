import "./App.css";

function App() {
  return (
    <main className="page-shell">
      <article className="project-card" aria-labelledby="project-title">
        <header>
          <p className="eyebrow">Research platform</p>
          <h1 id="project-title">DriveGuard Lab</h1>
          <p className="subtitle">Intelligent Driving Risk Simulation Lab</p>
        </header>

        <section aria-labelledby="status-heading">
          <h2 id="status-heading">Current status</h2>
          <p className="status">Foundation initialized</p>
          <p>
            This project is intended for repeatable simulation research. Vehicle
            control algorithms have not been implemented yet.
          </p>
        </section>

        <aside className="safety-notice" aria-labelledby="safety-heading">
          <h2 id="safety-heading">Safety notice</h2>
          <p>
            For software learning and simulation experiments only. Do not use this
            software to control a real vehicle.
          </p>
        </aside>
      </article>
    </main>
  );
}

export default App;
