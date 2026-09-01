"use client";

import {
  BookOpen,
  Check,
  ChevronRight,
  Compass,
  Flame,
  Headphones,
  Library,
  Menu,
  Mic2,
  Moon,
  Play,
  Plus,
  Send,
  Sparkles,
  Sun,
  UserRound,
  Volume2,
  X,
} from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import {
  createUrlImport,
  getAccessToken,
  getImport,
  listImports,
  login,
  submitDictation,
  uploadMedia,
  type DictationResult,
  type ImportJob,
} from "../lib/api";

type Section = "今日" | "沉浸" | "复习" | "词库" | "我";

const navigation: { label: Section; icon: typeof Compass }[] = [
  { label: "今日", icon: Compass },
  { label: "沉浸", icon: Play },
  { label: "复习", icon: BookOpen },
  { label: "词库", icon: Library },
  { label: "我", icon: UserRound },
];

const practiceSteps = ["精听", "听写", "跟读", "角色扮演"];

export default function Home() {
  const [active, setActive] = useState<Section>("今日");
  const [dark, setDark] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [toast, setToast] = useState("");
  const [dictation, setDictation] = useState("");
  const [checked, setChecked] = useState(false);
  const [dictationResult, setDictationResult] = useState<DictationResult | null>(null);
  const [loginOpen, setLoginOpen] = useState(false);
  const [signedIn, setSignedIn] = useState(
    () => typeof window !== "undefined" && Boolean(getAccessToken()),
  );
  const [submitting, setSubmitting] = useState(false);
  const [importJob, setImportJob] = useState<ImportJob | null>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [dark]);

  useEffect(() => {
    if (!signedIn) return;
    listImports()
      .then((jobs) => setImportJob((current) => current ?? jobs[0] ?? null))
      .catch((error: unknown) => notify(error instanceof Error ? error.message : "无法恢复导入任务"));
  }, [signedIn]);

  useEffect(() => {
    if (!importJob || ["ready", "failed", "cancelled"].includes(importJob.status)) return;
    const timer = window.setInterval(() => {
      getImport(importJob.id).then(setImportJob).catch((error: unknown) => {
        notify(error instanceof Error ? error.message : "无法读取导入进度");
      });
    }, 2000);
    return () => window.clearInterval(timer);
  }, [importJob]);

  function notify(message: string) {
    setToast(message);
    window.setTimeout(() => setToast(""), 3200);
  }

  async function submitImport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const sourceUrl = formData.get("source_url")?.toString() ?? "";
    const file = formData.get("video_file");
    const subtitle = formData.get("subtitle_file");
    setSubmitting(true);
    try {
      if (!sourceUrl && !(file instanceof File && file.size > 0)) {
        throw new Error("请粘贴 HTTPS 视频链接或选择视频文件");
      }
      const job = file instanceof File && file.size > 0
        ? await uploadMedia(file, subtitle instanceof File && subtitle.size > 0 ? subtitle : undefined)
        : await createUrlImport(sourceUrl);
      setImportJob(job);
      setDialogOpen(false);
      notify("视频已加入处理队列，正在准备学习材料。");
    } catch (error) {
      notify(error instanceof Error ? error.message : "导入失败，请稍后重试。");
    } finally {
      setSubmitting(false);
    }
  }

  async function submitLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await login(form.get("email")?.toString() ?? "", form.get("password")?.toString() ?? "");
      setSignedIn(true); setLoginOpen(false); notify("Owner 登录成功。");
    } catch (error) { notify(error instanceof Error ? error.message : "登录失败"); }
  }

  return (
    <main className="app-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar--open" : ""}`} aria-label="主导航">
        <div className="brand"><Sparkles aria-hidden /> <span>Verbaia</span></div>
        <p className="brand-note">你的英语沉浸空间</p>
        <nav>
          {navigation.map(({ label, icon: Icon }) => (
            <button className={`nav-item ${active === label ? "is-active" : ""}`} key={label} onClick={() => { setActive(label); setMenuOpen(false); }}>
              <Icon aria-hidden size={20} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="theme-toggle" onClick={() => setDark((value) => !value)} aria-label="切换明暗主题">
            {dark ? <Sun size={18} /> : <Moon size={18} />} {dark ? "浅色" : "深色"}
          </button>
          <button className="identity" onClick={() => setLoginOpen(true)}><span>WZ</span><div><strong>{signedIn ? "Wenjie" : "登录 Owner"}</strong><small>{signedIn ? "个人学习空间" : "访问学习资料"}</small></div></button>
        </div>
      </aside>

      {menuOpen && <button className="scrim" aria-label="关闭导航" onClick={() => setMenuOpen(false)} />}

      <section className="content">
        <header className="topbar">
          <button className="icon-button mobile-menu" aria-label="打开导航" onClick={() => setMenuOpen(true)}><Menu /></button>
          <div><p className="eyebrow">MONDAY · 31 AUG</p><h1>{active === "今日" ? "今天，学一点真英语。" : active}</h1></div>
          <button className="primary-button top-action" onClick={() => setDialogOpen(true)}><Plus size={18} /> 导入视频</button>
        </header>

        <section className="overview-grid" aria-label="今日学习概览">
          <article className="hero-card">
            <div className="hero-copy"><p className="eyebrow">TODAY&apos;S FOCUS</p><h2>从一段真实对话，开始你的沉浸练习。</h2><p>完成 18 分钟精听、听写与跟读，建立可复用的表达。</p><button className="primary-button" onClick={() => setActive("沉浸")}>继续学习 <ChevronRight size={18} /></button></div>
            <div className="hero-orbit" aria-hidden><span>18</span><small>分钟</small></div>
          </article>
          <article className="streak-card"><Flame aria-hidden /><p>连续学习</p><strong>12 <small>天</small></strong><div className="week" aria-label="本周学习记录">{[1, 1, 1, 1, 1, 0, 0].map((done, index) => <span className={done ? "done" : ""} key={index} />)}</div></article>
        </section>

        <section className="section-heading"><div><p className="eyebrow">IMMERSION PATH</p><h2>正在进行</h2></div><button className="text-button" onClick={() => setActive("沉浸")}>查看全部 <ChevronRight size={16} /></button></section>
        {importJob && <p className="import-status" role="status">导入进度：{importJob.progress}% · {importJob.message}</p>}
        <article className="lesson-card">
          <div className="video-cover"><span className="cover-label">BBC LEARNING</span><button className="play-button" aria-label="播放本课" onClick={() => notify("已从 06:42 继续播放。")}><Play fill="currentColor" /></button><span className="duration">12:48</span></div>
          <div className="lesson-detail"><div className="lesson-meta"><span className="tag">B1 · en-GB</span><span>上次学习于今天 09:18</span></div><h3>How cities can become more liveable</h3><p>从城市生活议题中练习观点表达与自然连读。</p><div className="progress-line"><span style={{ width: "62%" }} /></div><div className="lesson-bottom"><strong>已完成 62%</strong><button className="outline-button" onClick={() => setActive("沉浸")}>继续 <ChevronRight size={16} /></button></div></div>
        </article>

        <section className="section-heading practice-heading"><div><p className="eyebrow">ONE SENTENCE AT A TIME</p><h2>今日微练习</h2></div><span className="subtle-count">4 个步骤</span></section>
        <section className="practice-grid">
          {practiceSteps.map((step, index) => {
            const icons = [Headphones, Volume2, Mic2, Send];
            const Icon = icons[index];
            return <button className="practice-card" key={step} onClick={() => notify(`${step}练习已准备好。`)}><span className="practice-index">0{index + 1}</span><Icon aria-hidden /><strong>{step}</strong><small>{["听懂语块", "补全句子", "模仿节奏", "开口回应"][index]}</small></button>;
          })}
        </section>

        <section className="review-panel" aria-labelledby="dictation-title">
          <div><p className="eyebrow">QUICK CHECK</p><h2 id="dictation-title">听写一句</h2><p className="quote">“The best way to learn is to stay curious.”</p><button className="sound-button" onClick={() => notify("正在播放示范音频。")}><Volume2 size={17} /> 播放 0:06</button></div>
          <form onSubmit={async (event) => { event.preventDefault(); try { const result = await submitDictation(dictation, "The best way to learn is to stay curious."); setDictationResult(result); setChecked(true); } catch (error) { notify(error instanceof Error ? error.message : "听写提交失败"); } }}><label htmlFor="dictation">听到什么？</label><div className="input-row"><input id="dictation" value={dictation} onChange={(event) => { setDictation(event.target.value); setChecked(false); setDictationResult(null); }} placeholder="输入你听到的英文…" /><button className="primary-button" type="submit">检查</button></div>{checked && <p className="feedback"><Check size={16} /> {dictationResult ? <>得分 {dictationResult.score} 分{dictationResult.missed_words.length ? <>，漏掉 <em>{dictationResult.missed_words.join(", ")}</em></> : "，完全正确！"}</> : "正在计算…"}</p>}</form>
        </section>
      </section>

      <nav className="bottom-nav" aria-label="移动端主导航">{navigation.map(({ label, icon: Icon }) => <button key={label} className={active === label ? "is-active" : ""} onClick={() => setActive(label)}><Icon size={20} /><span>{label}</span></button>)}</nav>

      {dialogOpen && <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="import-title"><button className="scrim" aria-label="关闭导入窗口" onClick={() => setDialogOpen(false)} /><form className="import-modal" onSubmit={submitImport}><div className="modal-heading"><div><p className="eyebrow">NEW IMMERSION</p><h2 id="import-title">导入一段英语视频</h2></div><button type="button" className="icon-button" aria-label="关闭" onClick={() => setDialogOpen(false)}><X /></button></div><label htmlFor="video-url">HTTPS 视频链接</label><input id="video-url" name="source_url" type="url" placeholder="https://www.youtube.com/watch?..." /><p className="form-note">或选择本地视频文件（MP4、WebM、MOV、M4V）。二选一即可。</p><label htmlFor="video-file">视频文件</label><input id="video-file" name="video_file" type="file" accept="video/mp4,video/webm,video/quicktime,video/x-m4v" /><label htmlFor="subtitle-file">字幕文件（可选）</label><input id="subtitle-file" name="subtitle_file" type="file" accept=".srt,.vtt,text/vtt,application/x-subrip" /><p className="form-note">可同时上传 SRT/VTT；未提供字幕时将尝试外部英语转写。</p><div className="modal-actions"><button type="button" className="text-button" onClick={() => setDialogOpen(false)}>取消</button><button className="primary-button" disabled={submitting} type="submit">{submitting ? "提交中…" : "加入队列"} <ChevronRight size={17} /></button></div></form></div>}
      {loginOpen && <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="login-title"><button className="scrim" aria-label="关闭登录窗口" onClick={() => setLoginOpen(false)} /><form className="import-modal" onSubmit={submitLogin}><div className="modal-heading"><div><p className="eyebrow">OWNER ACCESS</p><h2 id="login-title">登录个人学习空间</h2></div><button type="button" className="icon-button" aria-label="关闭" onClick={() => setLoginOpen(false)}><X /></button></div><label htmlFor="owner-email">邮箱</label><input id="owner-email" name="email" type="email" required /><label htmlFor="owner-password">密码</label><input id="owner-password" name="password" type="password" minLength={12} required /><div className="modal-actions"><button className="primary-button" type="submit">登录</button></div></form></div>}
      {toast && <div className="toast" role="status"><Check size={18} /> {toast}</div>}
    </main>
  );
}
