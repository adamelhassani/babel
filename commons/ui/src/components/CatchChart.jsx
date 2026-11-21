import { useMemo } from "react";
import { Bar } from "react-chartjs-2";

export default function CatchChart({C, rec}) {
  const data = useMemo(() => {
    const labels = rec ? rec.fishers.map((f) => f.name) : [];
    return {
      labels,
      datasets: [
        {label: "catch", data: rec ? rec.fishers.map((f) => f.catch) : [], backgroundColor: "#e67e22", borderRadius: 4},
        {label: "report", data: rec ? rec.fishers.map((f) => f.report) : [], backgroundColor: "#9b59b6", borderRadius: 4},
        {type: "line", label: "sustainable " + C.PER_FISHER_SUSTAINABLE, data: labels.map(() => C.PER_FISHER_SUSTAINABLE), borderColor: "#34d399", borderDash: [6, 6], pointRadius: 0, fill: false},
      ],
    };
  }, [C, rec]);

  const options = useMemo(() => ({
    animation: {duration: 300},
    scales: {
      x: {ticks: {color: "#eee"}},
      y: {min: 0, max: C.C_MAX, ticks: {color: "#eee"}},
    },
    plugins: {legend: {labels: {color: "#eee"}}},
  }), [C]);

  return <Bar data={data} options={options} />;
}
