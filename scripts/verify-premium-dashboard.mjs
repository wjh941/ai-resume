import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

const dashboardPath = path.resolve(import.meta.dirname, '..', 'premium-dashboard.html');
const html = fs.readFileSync(dashboardPath, 'utf8');
const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)].map(match => match[1]);
assert.equal(scripts.length, 1, 'dashboard must keep one inline script');

const storage = new Map();
const sandbox = {
  console,
  crypto: { randomUUID: () => 'test-id' },
  localStorage: {
    failKey: '',
    get length() { return storage.size; },
    key(index) { return [...storage.keys()][index] ?? null; },
    getItem(key) { return storage.get(String(key)) ?? null; },
    setItem(key, value) { if (this.failKey === String(key)) throw new Error('quota'); storage.set(String(key), String(value)); },
    removeItem(key) { storage.delete(String(key)); }
  },
  navigator: { onLine: true },
  setTimeout,
  clearTimeout
};
sandbox.globalThis = sandbox;

const exportApi = `
globalThis.__dashboardTestApi = {
  safeJsonParse,
  saveLocal,
  saveLocalBatch,
  maskSensitiveText,
  filterJobs,
  reorderByIds: typeof reorderByIds === 'function' ? reorderByIds : undefined,
  maskTextExport: typeof maskTextExport === 'function' ? maskTextExport : undefined,
  cleanupOldDrafts: typeof cleanupOldDrafts === 'function' ? cleanupOldDrafts : undefined,
  cleanupExpiredDeliveries: typeof cleanupExpiredDeliveries === 'function' ? cleanupExpiredDeliveries : undefined,
  calendarMonthDays: typeof calendarMonthDays === 'function' ? calendarMonthDays : undefined,
  interviewNotesKey: typeof interviewNotesKey === 'function' ? interviewNotesKey : undefined,
  compareAssessments: typeof compareAssessments === 'function' ? compareAssessments : undefined,
  assessmentPlanningText: typeof assessmentPlanningText === 'function' ? assessmentPlanningText : undefined,
  validateShortcuts: typeof validateShortcuts === 'function' ? validateShortcuts : undefined,
  deliveryStats: typeof deliveryStats === 'function' ? deliveryStats : undefined,
  mergeRestoredExtension: typeof mergeRestoredExtension === 'function' ? mergeRestoredExtension : undefined,
  removeEvidenceAttachments: typeof removeEvidenceAttachments === 'function' ? removeEvidenceAttachments : undefined,
  state
};`;
const source = scripts[0].replace(/\n\s*initialize\(\);\s*$/, exportApi);
assert.doesNotThrow(() => new Function(source), 'inline script must compile');
vm.runInNewContext(source, sandbox, { filename: 'premium-dashboard.inline.js' });

const api = sandbox.__dashboardTestApi;
assert.equal(api.safeJsonParse('{"ok":true}', null).ok, true);
assert.equal(api.safeJsonParse('{', 'fallback'), 'fallback');
assert.equal(api.saveLocalBatch([['batch-one', { ok: true }], ['batch-two', { ok: true }]]), true);
sandbox.localStorage.failKey = 'batch-fail';
assert.equal(api.saveLocalBatch([['batch-restore', { changed: true }], ['batch-fail', { changed: true }]]), false);
assert.equal(sandbox.localStorage.getItem('batch-restore'), null);
sandbox.localStorage.failKey = '';
assert.equal(api.maskSensitiveText('13800000000', true), '138****0000');
assert.equal(api.maskSensitiveText('name@example.com', true), 'n***@example.com');
assert.deepEqual(
  api.filterJobs([
    { roleName: 'A', family: 'data', score: 80, salary: '10k-15k', city: 'Shanghai' },
    { roleName: 'B', family: 'product', score: 70, salary: '6k-8k', city: 'Hangzhou' }
  ], { salaryMin: '12', salaryMax: '', family: 'data', city: 'shang', difficulty: 'medium' }).map(item => item.roleName),
  ['A']
);
assert.equal(typeof api.reorderByIds, 'function', 'reorderByIds must exist for durable drag priorities');
assert.deepEqual(
  api.reorderByIds([{ id: 'a' }, { id: 'b' }, { id: 'c' }], ['c', 'a'], item => item.id).map(item => item.id),
  ['c', 'a', 'b']
);

assert.equal(typeof api.maskTextExport, 'function');
api.state.extension.maskSensitive = true;
api.state.resume = { name: 'Alice Chen', phone: '13800000000', email: 'alice@example.com' };
assert.equal(api.maskTextExport('Alice Chen 13800000000 alice@example.com'), 'A********n 138****0000 a***@example.com');
assert.equal(typeof api.cleanupOldDrafts, 'function');
assert.equal(typeof api.cleanupExpiredDeliveries, 'function');
api.state.drafts = [{ id: 'draft-1' }, { id: 'draft-2' }, { id: 'draft-3' }];
assert.equal(api.cleanupOldDrafts(2), 1);
assert.deepEqual(Array.from(api.state.drafts, item => item.id), ['draft-1', 'draft-2']);
api.state.deliveries = [{ id: 1, status: 'applied', nextActionAt: '2026-01-01' }, { id: 2, status: 'closed', nextActionAt: '2026-01-01' }, { id: 3, status: 'closed', nextActionAt: '2026-03-01' }];
assert.equal(api.cleanupExpiredDeliveries('2026-02-01'), 1);
assert.deepEqual(Array.from(api.state.deliveries, item => item.id), [1, 3]);
api.state.deliveries = [{ status: 'interview', appliedDate: '2026-02-01' }, { status: 'offer', appliedDate: '2026-02-02' }, { status: 'applied', appliedDate: '2026-02-03' }];
assert.equal(api.deliveryStats?.().interviewRate, 50);
assert.equal(api.deliveryStats?.().offerRate, 33);
assert.equal(typeof api.mergeRestoredExtension, 'function');
const mergedExtension = api.mergeRestoredExtension({ favoriteJobs: [{ roleName: 'Imported' }] }, { snapshots: [{ id: 'protect' }], backups: [{ id: 'export' }], favoriteJobs: [] });
assert.deepEqual(Array.from(mergedExtension.favoriteJobs, item => item.roleName), ['Imported']);
assert.deepEqual(JSON.parse(JSON.stringify(mergedExtension.snapshots)), [{ id: 'protect' }]);
assert.deepEqual(JSON.parse(JSON.stringify(mergedExtension.backups)), [{ id: 'export' }]);
assert.equal(typeof api.removeEvidenceAttachments, 'function');
api.state.extension.evidenceAttachments = { 1: [{ id: 'file' }], 2: [{ id: 'keep' }] };
api.removeEvidenceAttachments([1]);
assert.deepEqual(JSON.parse(JSON.stringify(api.state.extension.evidenceAttachments)), { 2: [{ id: 'keep' }] });
assert.deepEqual(Array.from(api.calendarMonthDays?.(2026, 1).slice(0, 3) || []), [1, 2, 3]);
assert.equal(api.interviewNotesKey?.('delivery-1', 2), 'delivery-1:2');
assert.equal(JSON.stringify(api.compareAssessments?.({ score: 80 }, { score: 70 })), JSON.stringify({ scoreDelta: 10, roles: [[], []] }));
assert.match(api.assessmentPlanningText?.({ action_plan: {} }) || '', /职业规划/);
assert.equal(api.validateShortcuts?.({ save: 's', export: 's' }), '快捷键不能重复');
assert.match(html, /function attachSortable\b/);
assert.match(html, /data-draft-sort/);
assert.match(html, /data-favorite-sort/);
assert.match(html, /data-template-section/);
assert.match(html, /data-evidence-batch-check/);
assert.match(html, /function renderMonthlyDeliveryCalendar\b/);
assert.match(html, /function openChangelog\b/);
assert.match(html, /footer\.id\s*=\s*"releaseFooter"/);
assert.match(html, /面试通过率/);
assert.match(html, /openEvidenceOrganizerToolbarBtn/);
assert.match(html, /items\.length && isExpiredDate\(date\)/);
assert.match(html, /图片附件未保存，请释放本地空间后重试/);
assert.match(html, /function saveLocalBatch\b/);

console.log('premium dashboard contract checks passed');
