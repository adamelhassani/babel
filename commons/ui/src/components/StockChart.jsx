import { useMemo } from "react";
import { Line } from "react-chartjs-2";

function ruleMarkerRounds(rounds) {
  const markers = new Set();
  for (let i = 0; i < rounds.length; i++) {
    const r = rounds[i].rule;
    const prev = i > 0 ? rounds[i - 1].rule : null;
    if (r && (!prev || JSON.stringify(prev) !== JSON.stringify(r))) markers.add(rounds[i].round);
  }
  return markers;
}

export default function StockChart({C, rounds, cur}) {
  const data = useMemo(() => {
    const seen = rounds.slice(0, cur);
    const labels = seen.map((r) => r.round);
    const markers = ruleMarkerRounds(rounds);
    return {
      labels,
      datasets: [
        {label: "stock", data: seen.map((r) => r.stock_after), borderColor: "#38bdf8", backgroundColor: "rgba(56,189,248,.15)", fill: true, pointRadius: 2, tension: 0.25},
        {label: "Healthy level (" + C.K / 2 + ")", data: labels.map(() => C.K / 2), borderColor: "#888", borderDash: [6, 6], pointRadius: 0, fill: false},
        {label: "rule applied", data: labels.map((l) => (markers.has(l) ? C.K * 0.97 : null)), showLine: false, pointRadius: 7, pointStyle: "triangle", pointBackgroundColor: "#fbbf24", fill: false},
      ],
    };
  }, [C, rounds, cur]);

  const options = useMemo(() => ({
    animation: {duration: 300},
    scales: {
      x: {ticks: {color: "#eee"}},
      y: {min: 0, max: C.K, ticks: {color: "#eee"}},
    },
    plugins: {
      legend: {labels: {color: "#eee"}},
      tooltip: {
        callbacks: {
          afterBody: (items) => {
            const it = items.find((x) => x.datasetIndex === 2 && x.parsed.y != null);
            if (!it) return [];
            const rec = rounds[it.dataIndex];
            return rec && rec.rule ? ["rule: " + rec.rule.plain_text] : [];
          },
        },
      },
    },
  }), [C, rounds]);

  return <Line data={data} options={options} />;
}
