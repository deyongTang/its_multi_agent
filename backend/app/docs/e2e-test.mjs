import { chromium } from 'playwright';

const API = 'http://127.0.0.1:8000/api/query';
const TIMEOUT = 120_000;

// ── Test Cases ──
const cases = [
  {
    id: 'TC-01', name: '闲聊场景',
    input: '你好，今天天气真不错',
    assert(ctx) {
      return [
        check('出现 general_chat', ctx.processes.some(p => p.includes('general_chat'))),
        check('无 slot_filling', !ctx.processes.some(p => p.includes('slot_filling'))),
        check('无 retrieval', !ctx.processes.some(p => p.includes('retrieval'))),
        check('有友好回复', ctx.answer.length > 5),
      ];
    }
  },
  {
    id: 'TC-02', name: '槽位不完整追问',
    input: '电脑蓝屏了',
    assert(ctx) {
      return [
        check('出现 ask_user', ctx.processes.some(p => p.includes('ask_user'))),
        check('无 retrieval', !ctx.processes.some(p => p.includes('retrieval'))),
        check('返回追问话术', ctx.answer.length > 5),
        check('is_ask_user=true', ctx.hasAskUser),
      ];
    }
  },
  {
    id: 'TC-05', name: '升级人工',
    input: 'xyzabc123 型号主板烧了怎么修',
    assert(ctx) {
      return [
        check('出现 escalate', ctx.processes.some(p => p.includes('escalate'))),
        check('包含人工客服话术', /人工|客服|转接|工程师|抱歉/.test(ctx.answer)),
        check('无 generate_report', !ctx.processes.some(p => p.includes('generate_report'))),
      ];
    }
  },
  {
    id: 'TC-06', name: '服务站查询',
    input: '北京朝阳区附近有联想服务站吗',
    assert(ctx) {
      return [
        check('出现 retrieval', ctx.processes.some(p => p.includes('retrieval'))),
        check('包含服务站信息', /服务站|地址|电话|联想/.test(ctx.answer)),
        check('有回复内容', ctx.answer.length > 10),
      ];
    }
  },
  {
    id: 'TC-07', name: 'POI导航',
    input: '帮我导航到联想北京总部',
    assert(ctx) {
      return [
        check('调用地图工具', ctx.processes.some(p => /map|地图|poi|导航|工具/.test(p))),
        check('包含地点信息', /地址|位置|联想|北京/.test(ctx.answer)),
        check('有回复内容', ctx.answer.length > 10),
      ];
    }
  },
];

function check(name, ok) { return { name, ok }; }

// ── Main ──
(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:8000/docs');

  console.log('\n🚀 ITS 多智能体全链路测试开始\n');
  console.log('='.repeat(60));

  let totalPass = 0, totalFail = 0;

  for (const tc of cases) {
    console.log(`\n▶ ${tc.id} ${tc.name}`);
    console.log(`  输入: "${tc.input}"`);

    try {
      const ctx = await runInBrowser(page, tc.input);

      // Print events
      console.log(`  流程节点: ${ctx.processes.join(' → ')}`);
      console.log(`  回复(前100字): ${ctx.answer.slice(0, 100)}...`);

      // Run assertions
      const results = tc.assert(ctx);
      let allPass = true;
      for (const r of results) {
        const icon = r.ok ? '✅' : '❌';
        console.log(`  ${icon} ${r.name}`);
        if (!r.ok) allPass = false;
      }

      if (allPass) { totalPass++; console.log(`  ✅ ${tc.id} 通过`); }
      else { totalFail++; console.log(`  ❌ ${tc.id} 失败`); }

    } catch (err) {
      totalFail++;
      console.log(`  ❌ 错误: ${err.message}`);
    }

    console.log('-'.repeat(60));
  }

  console.log('\n' + '='.repeat(60));
  console.log(`📊 结果: ${totalPass} 通过 / ${totalFail} 失败 / ${cases.length} 总计`);
  console.log('='.repeat(60) + '\n');

  await browser.close();
  process.exit(totalFail > 0 ? 1 : 0);
})();

// ── Browser SSE Execution ──
async function runInBrowser(page, query) {
  const sid = `test_${Date.now()}`;

  const result = await page.evaluate(async ({ api, query, sid, timeout }) => {
    const ctx = { processes: [], answer: '', hasAskUser: false };

    const resp = await fetch(api, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, context: { user_id: 'test_user', session_id: sid } })
    });

    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    const start = Date.now();

    while (true) {
      if (Date.now() - start > timeout) throw new Error('Timeout');
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.startsWith('data:')) continue;
        try {
          const pkt = JSON.parse(line.slice(5).trim());
          const c = pkt.content || {};
          const kind = (c.kind || '').toUpperCase();
          const text = c.text || '';

          if (kind === 'PROCESS') ctx.processes.push(text);
          else if (kind === 'ANSWER') ctx.answer += text;
          if (pkt.is_ask_user) ctx.hasAskUser = true;
        } catch {}
      }
    }

    return ctx;
  }, { api: API, query, sid, timeout: TIMEOUT });

  return result;
}
