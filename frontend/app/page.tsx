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
import { FormEvent, useEffect, useRef, useState } from "react";
import {
  createUrlImport,
  getAccessToken,
  getImport,
  getImportEvents,
  getMediaObjectUrl,
  getTranscript,
  getRolePlaySession,
  getWritingAttempt,
  createRolePlaySession,
  listImports,
  listVocabularyItems,
  login,
  logout,
  submitDictation,
  submitRolePlayTurn,
  submitWriting,
  uploadMedia,
  saveVideoProgress,
  reviewVocabulary,
  type DictationResult,
  type ImportEvent,
  type ImportJob,
  type RolePlaySession,
  type TranscriptSegment,
  type WritingAttempt,
  type VocabularyItem,
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
  const [importEvents, setImportEvents] = useState<ImportEvent[]>([]);
  const [media, setMedia] = useState<{ assetId: string; url: string } | null>(null);
  const [transcript, setTranscript] = useState<{ jobId: string; segments: TranscriptSegment[] } | null>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const [rolePlayOpen, setRolePlayOpen] = useState(false);
  const [rolePlay, setRolePlay] = useState<RolePlaySession | null>(null);
  const [roleMessage, setRoleMessage] = useState("");
  const [writingOpen, setWritingOpen] = useState(false);
  const [writing, setWriting] = useState<WritingAttempt | null>(null);
  const [writingDraft, setWritingDraft] = useState("");
  const [vocabulary, setVocabulary] = useState<VocabularyItem[]>([]);
  const writingPrompt = "Describe one small change that could make your city more liveable.";
  const importJobId = importJob?.id;

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
    if (!signedIn) return;
    listVocabularyItems().then(setVocabulary).catch((error: unknown) => {
      notify(error instanceof Error ? error.message : "无法读取词库");
    });
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

  useEffect(() => {
    if (!importJob) return;
    getImportEvents(importJob.id).then(setImportEvents).catch(() => undefined);
  }, [importJob]);

  useEffect(() => {
    if (!importJob?.media_asset_id) return;
    let active = true;
    let objectUrl: string | null = null;
    getMediaObjectUrl(importJob.media_asset_id).then((url) => {
      objectUrl = url;
      if (active) setMedia({ assetId: importJob.media_asset_id!, url }); else URL.revokeObjectURL(url);
    }).catch((error: unknown) => notify(error instanceof Error ? error.message : "无法加载视频"));
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [importJob?.media_asset_id]);

  useEffect(() => {
    if (!importJobId) return;
    getTranscript(importJobId).then((segments) => setTranscript({ jobId: importJobId, segments })).catch(() => undefined);
  }, [importJobId]);

  useEffect(() => {
    if (!rolePlay || rolePlay.status !== "waiting_for_reply") return;
    const timer = window.setInterval(() => {
      getRolePlaySession(rolePlay.id).then(setRolePlay).catch((error: unknown) => {
        notify(error instanceof Error ? error.message : "无法读取角色扮演回复");
      });
    }, 1800);
    return () => window.clearInterval(timer);
  }, [rolePlay]);

  useEffect(() => {
    if (!writing || !["queued", "processing"].includes(writing.evaluation_status)) return;
    const timer = window.setInterval(() => {
      getWritingAttempt(writing.id).then(setWriting).catch((error: unknown) => {
        notify(error instanceof Error ? error.message : "无法读取写作反馈");
      });
    }, 1800);
    return () => window.clearInterval(timer);
  }, [writing]);

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

  async function signOut() {
    await logout();
    setSignedIn(false); setImportJob(null); setLoginOpen(false); notify("已安全退出 Owner 会话。");
  }

  async function openRolePlay() {
    try { setRolePlay(await createRolePlaySession("Ordering coffee at a busy cafe")); setRolePlayOpen(true); }
    catch (error) { notify(error instanceof Error ? error.message : "无法开始角色扮演"); }
  }

  async function sendRolePlay(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!rolePlay || !roleMessage.trim()) return;
    try { setRolePlay(await submitRolePlayTurn(rolePlay.id, roleMessage)); setRoleMessage(""); }
    catch (error) { notify(error instanceof Error ? error.message : "发送失败"); }
  }

  async function sendWriting(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!writingDraft.trim()) return;
    try {
      setWriting(await submitWriting(writingPrompt, writingDraft));
    } catch (error) { notify(error instanceof Error ? error.message : "写作提交失败"); }
  }

  function jumpToSegment(segment: TranscriptSegment) {
    if (!videoRef.current) return;
    videoRef.current.currentTime = segment.start_ms / 1000;
    void videoRef.current.play();
  }

  function persistVideoProgress() {
    const video = videoRef.current;
    if (!video || !importJob) return;
    saveVideoProgress(importJob.id, video.currentTime, video.duration).catch(() => undefined);
  }

  async function gradeVocabulary(item: VocabularyItem, grade: "again" | "hard" | "good" | "easy") {
    try {
      const updated = await reviewVocabulary(item.id, grade);
      setVocabulary((items) => items.map((current) => current.id === updated.id ? updated : current));
      notify(`已安排下次复习：${updated.interval_days} 天后。`);
    } catch (error) { notify(error instanceof Error ? error.message : "保存复习结果失败"); }
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
        {importJob?.status === "failed" && importEvents.length > 0 && <p className="import-error">{importEvents.at(-1)?.message}</p>}
        <article className="lesson-card">
          <div className="video-cover">{importJob?.media_asset_id && media?.assetId === importJob.media_asset_id ? <video ref={videoRef} className="lesson-video" controls preload="metadata" src={media.url} onPause={persistVideoProgress} onEnded={persistVideoProgress} /> : <><span className="cover-label">BBC LEARNING</span><button className="play-button" aria-label="播放本课" onClick={() => notify("请先导入本地视频后播放。")}><Play fill="currentColor" /></button><span className="duration">12:48</span></>}</div>
          <div className="lesson-detail"><div className="lesson-meta"><span className="tag">B1 · en-GB</span><span>上次学习于今天 09:18</span></div><h3>How cities can become more liveable</h3><p>从城市生活议题中练习观点表达与自然连读。</p><div className="progress-line"><span style={{ width: "62%" }} /></div><div className="lesson-bottom"><strong>已完成 62%</strong><button className="outline-button" onClick={() => setActive("沉浸")}>继续 <ChevronRight size={16} /></button></div></div>
        </article>
        {importJob?.media_asset_id && media?.assetId === importJob.media_asset_id && transcript?.jobId === importJob.id && transcript.segments.length > 0 && <section className="transcript-panel" aria-label="视频字幕"><p className="eyebrow">INTERACTIVE TRANSCRIPT</p><h2>点击字幕跳转练习</h2><div className="transcript-list">{transcript.segments.map((segment) => <button key={segment.id} onClick={() => jumpToSegment(segment)}><time>{`${Math.floor(segment.start_ms / 60000)}:${String(Math.floor(segment.start_ms / 1000) % 60).padStart(2, "0")}`}</time><span>{segment.text}</span></button>)}</div></section>}

        <section className="section-heading practice-heading"><div><p className="eyebrow">ONE SENTENCE AT A TIME</p><h2>今日微练习</h2></div><button className="text-button" onClick={() => { setWriting(null); setWritingOpen(true); }}>写作反馈 <ChevronRight size={16} /></button></section>
        <section className="practice-grid">
          {practiceSteps.map((step, index) => {
            const icons = [Headphones, Volume2, Mic2, Send];
            const Icon = icons[index];
            return <button className="practice-card" key={step} onClick={() => step === "角色扮演" ? openRolePlay() : notify(`${step}练习已准备好。`)}><span className="practice-index">0{index + 1}</span><Icon aria-hidden /><strong>{step}</strong><small>{["听懂语块", "补全句子", "模仿节奏", "开口回应"][index]}</small></button>;
          })}
        </section>

        {signedIn && <section className="vocabulary-panel" aria-labelledby="vocabulary-title"><div className="section-heading"><div><p className="eyebrow">PERSONAL VOCABULARY</p><h2 id="vocabulary-title">我的词库</h2></div><span className="subtle-count">{vocabulary.length} 个词</span></div>{vocabulary.length === 0 ? <p className="form-note">还没有保存的词汇。完成视频学习后可在这里持续复习。</p> : <div className="vocabulary-list">{vocabulary.slice(0, 6).map((item) => <article key={item.id}><div><strong>{item.term}</strong><p>{item.definition}</p><small>已复习 {item.repetitions} 次 · 间隔 {item.interval_days} 天</small></div><div className="review-grades"><button onClick={() => gradeVocabulary(item, "again")}>重来</button><button onClick={() => gradeVocabulary(item, "hard")}>困难</button><button onClick={() => gradeVocabulary(item, "good")}>掌握</button><button onClick={() => gradeVocabulary(item, "easy")}>简单</button></div></article>)}</div>}</section>}

        <section className="review-panel" aria-labelledby="dictation-title">
          <div><p className="eyebrow">QUICK CHECK</p><h2 id="dictation-title">听写一句</h2><p className="quote">“The best way to learn is to stay curious.”</p><button className="sound-button" onClick={() => notify("正在播放示范音频。")}><Volume2 size={17} /> 播放 0:06</button></div>
          <form onSubmit={async (event) => { event.preventDefault(); try { const result = await submitDictation(dictation, "The best way to learn is to stay curious."); setDictationResult(result); setChecked(true); } catch (error) { notify(error instanceof Error ? error.message : "听写提交失败"); } }}><label htmlFor="dictation">听到什么？</label><div className="input-row"><input id="dictation" value={dictation} onChange={(event) => { setDictation(event.target.value); setChecked(false); setDictationResult(null); }} placeholder="输入你听到的英文…" /><button className="primary-button" type="submit">检查</button></div>{checked && <p className="feedback"><Check size={16} /> {dictationResult ? <>得分 {dictationResult.score} 分{dictationResult.missed_words.length ? <>，漏掉 <em>{dictationResult.missed_words.join(", ")}</em></> : "，完全正确！"}</> : "正在计算…"}</p>}</form>
        </section>
      </section>

      <nav className="bottom-nav" aria-label="移动端主导航">{navigation.map(({ label, icon: Icon }) => <button key={label} className={active === label ? "is-active" : ""} onClick={() => setActive(label)}><Icon size={20} /><span>{label}</span></button>)}</nav>

      {dialogOpen && <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="import-title"><button className="scrim" aria-label="关闭导入窗口" onClick={() => setDialogOpen(false)} /><form className="import-modal" onSubmit={submitImport}><div className="modal-heading"><div><p className="eyebrow">NEW IMMERSION</p><h2 id="import-title">导入一段英语视频</h2></div><button type="button" className="icon-button" aria-label="关闭" onClick={() => setDialogOpen(false)}><X /></button></div><label htmlFor="video-url">HTTPS 视频链接</label><input id="video-url" name="source_url" type="url" placeholder="https://www.youtube.com/watch?..." /><p className="form-note">或选择本地视频文件（MP4、WebM、MOV、M4V）。二选一即可。</p><label htmlFor="video-file">视频文件</label><input id="video-file" name="video_file" type="file" accept="video/mp4,video/webm,video/quicktime,video/x-m4v" /><label htmlFor="subtitle-file">字幕文件（可选）</label><input id="subtitle-file" name="subtitle_file" type="file" accept=".srt,.vtt,text/vtt,application/x-subrip" /><p className="form-note">可同时上传 SRT/VTT；未提供字幕时将尝试外部英语转写。</p><div className="modal-actions"><button type="button" className="text-button" onClick={() => setDialogOpen(false)}>取消</button><button className="primary-button" disabled={submitting} type="submit">{submitting ? "提交中…" : "加入队列"} <ChevronRight size={17} /></button></div></form></div>}
      {loginOpen && <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="login-title"><button className="scrim" aria-label="关闭登录窗口" onClick={() => setLoginOpen(false)} /><form className="import-modal" onSubmit={submitLogin}><div className="modal-heading"><div><p className="eyebrow">OWNER ACCESS</p><h2 id="login-title">{signedIn ? "个人学习空间" : "登录个人学习空间"}</h2></div><button type="button" className="icon-button" aria-label="关闭" onClick={() => setLoginOpen(false)}><X /></button></div>{signedIn ? <div className="modal-actions"><button className="text-button" type="button" onClick={signOut}>退出登录</button></div> : <><label htmlFor="owner-email">邮箱</label><input id="owner-email" name="email" type="email" required /><label htmlFor="owner-password">密码</label><input id="owner-password" name="password" type="password" minLength={12} required /><div className="modal-actions"><button className="primary-button" type="submit">登录</button></div></>}</form></div>}
      {rolePlayOpen && rolePlay && <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="role-play-title"><button className="scrim" aria-label="关闭角色扮演" onClick={() => setRolePlayOpen(false)} /><form className="import-modal" onSubmit={sendRolePlay}><div className="modal-heading"><div><p className="eyebrow">ROLE PLAY</p><h2 id="role-play-title">{rolePlay.scenario}</h2></div><button type="button" className="icon-button" aria-label="关闭" onClick={() => setRolePlayOpen(false)}><X /></button></div><p className="form-note">用英语点一杯咖啡。{rolePlay.status === "waiting_for_reply" ? "AI 正在准备回复…" : rolePlay.status === "failed" ? "AI 回复失败，请稍后重试。" : ""}</p>{rolePlay.messages.map((message, index) => <p className="role-message" key={index}><strong>{message.speaker === "learner" ? "你" : "AI"}：</strong>{message.content}</p>)}<label htmlFor="role-message">你的英文回应</label><input id="role-message" value={roleMessage} onChange={(event) => setRoleMessage(event.target.value)} placeholder="Could I have a latte, please?" /><div className="modal-actions"><button className="primary-button" disabled={rolePlay.status === "waiting_for_reply"} type="submit">发送</button></div></form></div>}
      {writingOpen && <div className="modal-layer" role="dialog" aria-modal="true" aria-labelledby="writing-title"><button className="scrim" aria-label="关闭写作反馈" onClick={() => setWritingOpen(false)} /><form className="import-modal" onSubmit={sendWriting}><div className="modal-heading"><div><p className="eyebrow">WRITING CHECK</p><h2 id="writing-title">用英语表达观点</h2></div><button type="button" className="icon-button" aria-label="关闭" onClick={() => setWritingOpen(false)}><X /></button></div><p className="writing-prompt">{writingPrompt}</p><label htmlFor="writing-draft">你的回答</label><textarea id="writing-draft" value={writingDraft} onChange={(event) => setWritingDraft(event.target.value)} placeholder="I think my city could..." minLength={20} required />{["queued", "processing"].includes(writing?.evaluation_status ?? "") ? <p className="form-note">正在生成逐条反馈…</p> : null}{writing?.evaluation_status === "failed" && <p className="import-error">{writing.evaluation_error ?? "反馈生成失败，请稍后重试。"}</p>}{writing?.feedback && <div className="writing-feedback"><strong>{writing.clarity_score === null ? "反馈已生成" : `清晰度 ${writing.clarity_score} 分`}</strong>{writing.feedback.suggestions?.map((suggestion) => <p key={suggestion}>{suggestion}</p>)}{writing.feedback.corrected_draft && <p><em>更自然的表达：</em>{writing.feedback.corrected_draft}</p>}</div>}<div className="modal-actions"><button className="primary-button" disabled={["queued", "processing"].includes(writing?.evaluation_status ?? "")} type="submit">获取反馈</button></div></form></div>}
      {toast && <div className="toast" role="status"><Check size={18} /> {toast}</div>}
    </main>
  );
}
