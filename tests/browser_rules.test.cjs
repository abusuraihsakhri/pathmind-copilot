"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const html = fs.readFileSync("web/index.html", "utf8");
const match = html.match(/<script>([\s\S]*?)<\/script>/);
assert.ok(match, "inline application script exists");

const listeners = new Map();
const ids = [
    "runAuditButton", "downloadButton", "outputConsole", "m-tasks",
    "m-audit", "m-phi", "m-status", "modeBadge",
];
const elements = Object.fromEntries(ids.map((id) => [
    id,
    { textContent: "", disabled: false, addEventListener: (event, callback) => listeners.set(id + ":" + event, callback) }
]));
const context = vm.createContext({
    document: {
        getElementById: (id) => elements[id],
    },
    location: { hostname: "example.github.io", protocol: "https:" },
    console,
});
new vm.Script(match[1], { filename: "web/index.html" }).runInContext(context);
assert.equal(typeof listeners.get("runAuditButton:click"), "function");
assert.equal(typeof listeners.get("downloadButton:click"), "function");

function evaluate(primary, secondary, descriptor = "NOMINAL", critical = false) {
    return vm.runInContext(
        "localEvaluation(" + JSON.stringify({
            task_id: "TASK-TEST", target_identifier: "SPECIMEN-TEST",
            primary_metric: primary, secondary_metric: secondary,
            status_descriptor: descriptor, is_critical_flag: critical,
        }) + ")",
        context,
    );
}

const normal = evaluate(25, 12);
assert.equal(normal.overall_urgency, "ROUTINE");
assert.equal(normal.total_alerts, 0);
assert.equal(normal.audit_hash, null);
assert.equal(normal.evaluation_mode, "LOCAL_BROWSER_RULES_NOT_A_SIGNED_AUDIT");

const elevated = evaluate(25.01, 12.01, "FAIL");
assert.equal(elevated.overall_urgency, "ELEVATED_RISK");
assert.equal(elevated.total_alerts, 3);
assert.equal(elevated.integrity_status, "DISCORDANT_ANOMALY");

const critical = evaluate(0, 0, "NOMINAL", true);
assert.equal(critical.overall_urgency, "CRITICAL_STAT_PANIC");
assert.equal(critical.critical_alerts_count, 1);
assert.equal(critical.integrity_status, "RECALIBRATION_REQUIRED");
assert.equal(critical.audit_hash, null);
console.log("Browser rule smoke tests passed.");
