import TopBar from "./TopBar";
import RuleBar from "./RuleBar";
import LakeScene from "./LakeScene";
import StockChart from "./StockChart";
import CatchChart from "./CatchChart";
import ResultsTable from "./ResultsTable";
import InspectorPanel from "./InspectorPanel";

export default function DataView(p) {
  return (
    <>
      <TopBar {...p} />
      <RuleBar preview={p.preview} rec={p.rec} />
      <div className="panels">
        <div className="panel lake"><h3>Lake</h3><LakeScene C={p.C} rec={p.rec} ruleRound={p.ruleRound} onSpeak={p.onSpeak} /></div>
        <div className="panel"><h3>Stock over rounds</h3><StockChart C={p.C} rounds={p.rounds} cur={p.cur} /></div>
        <div className="panel"><h3>Catch vs report</h3><CatchChart C={p.C} rec={p.rec} /></div>
        <div className="panel"><h3>Results (avg by rule, sorted by rounds survived)</h3><ResultsTable batch={p.batch} /></div>
        <div className="panel"><h3>Inspector</h3><InspectorPanel inspector={p.inspector} runId={p.runId} /></div>
      </div>
    </>
  );
}
