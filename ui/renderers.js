// Renders the SAT question verdict: the formula judged, the answer given,
// and each constraint checked in order.
import { h, icon, statusPill } from "./kit/components.js";

export function renderSubmit(output) {
  const passed = output.verdict === "pass";
  const root   = h("div", { class: "sat-verdict" });

  const header = h("div", { class: "sat-header" });
  header.append(statusPill(passed ? "pass" : "fail", passed ? "ok" : "bad"));
  header.append(h("span", { class: "sat-score", text: `Score: ${output.score.toFixed(1)}` }));
  root.append(header);

  const list = h("ol", { class: "checks" });
  for (const c of output.constraints) {
    const item = h("li", { class: c.ok ? "check-ok" : "check-bad" });
    const head = h("div", { class: "check-head" });
    head.append(icon(c.ok ? "check-circle" : "x-circle"));
    head.append(h("span", { text: c.detail }));
    head.append(h("span", { class: "check-id", text: c.id }));
    item.append(head);
    list.append(item);
  }
  root.append(list);
  return root;
}

export default {
  SubmitOutput: renderSubmit,
};
