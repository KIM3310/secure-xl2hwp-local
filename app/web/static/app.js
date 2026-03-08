const cfg = window.UI_CONFIG || {};

const I18N = {
  ko: {
    "app.eyebrow": "LOCAL SECURE AUTOMATION",
    "app.title": "Secure XL2HWP Studio",
    "app.tagline": "엑셀 정제부터 한컴 문서화까지, 폐쇄망 친화형 자동화 스튜디오",
    "serviceBrief.kicker": "운영 계약",
    "serviceBrief.title": "서비스 브리프",
    "serviceBrief.subtitle": "운영 전 trust boundary, review flow, 처리 계약을 먼저 확인합니다.",
    "serviceBrief.loading": "불러오는 중...",
    "serviceBrief.unavailable": "서비스 브리프를 불러오지 못했습니다.",
    "serviceBrief.schema": "처리 스키마",
    "serviceBrief.authMode": "인증 모드",
    "serviceBrief.signing": "서명 모드",
    "serviceBrief.failedChecks": "실패 점검",
    "serviceBrief.roles": "처리 역할",
    "serviceBrief.reviewFlow": "검토 흐름",
    "serviceBrief.twoMinuteReview": "2분 검토 경로",
    "serviceBrief.trustBoundary": "신뢰 경계",
    "serviceBrief.proofAssets": "증거 자산",
    "serviceBrief.watchouts": "주의점",
    "reviewPack.title": "리뷰 패키지",
    "reviewPack.approvalGate": "승인 게이트",
    "reviewPack.proofBundle": "증거 번들",
    "reviewPack.boundary": "경계",
    "reviewPack.artifacts": "검토 산출물",
    "reviewPack.twoMinuteReview": "2분 검토 경로",
    "reviewPack.sequence": "검토 순서",
    "reviewPack.proofAssets": "증거 자산",
    "control.language": "언어",
    "control.theme": "테마",
    "control.brand": "브랜드",
    "auth.title": "인증",
    "auth.subtitle": "JWT 기반 접근 제어",
    "auth.userId": "사용자 ID",
    "auth.password": "비밀번호",
    "auth.login": "로그인",
    "auth.logout": "로그아웃",
    "auth.currentUser": "현재 로그인:",
    "auth.userPlaceholder": "local-admin",
    "auth.passwordPlaceholder": "StrongPassword!",
    "auth.bootstrapBadgeRequired": "관리자 설정 필요",
    "auth.bootstrapBadgeReady": "관리자 계정 준비됨",
    "auth.bootstrapTitle": "먼저 관리자 ID를 만드세요",
    "auth.bootstrapMessageRequired": "현재 로그인 가능한 계정이 없습니다. 아래 3단계를 따라 관리자 계정을 먼저 만들어 주세요.",
    "auth.bootstrapMessageReady": "활성 계정이 감지되었습니다. 생성한 관리자 계정으로 바로 로그인할 수 있습니다.",
    "auth.bootstrapRefresh": "상태 다시 확인",
    "auth.bootstrapStep1": ".env에서 AUTH_PASSWORD_PEPPER를 강한 값으로 설정합니다.",
    "auth.bootstrapStep2": "비밀번호 해시를 생성해 users.yaml에 등록합니다.",
    "auth.bootstrapStep3": "새로고침 후 생성한 관리자 계정으로 로그인합니다.",
    "auth.bootstrapRegistryLabel": "사용자 파일:",
    "auth.bootstrapHashLabel": "해시 생성 명령",
    "auth.bootstrapYamlLabel": "users.yaml 예시",
    "pipeline.title": "파이프라인 실행",
    "pipeline.subtitle": "Path 모드 / File 업로드 모드",
    "pipeline.modePath": "Path 모드",
    "pipeline.modeFile": "File 모드",
    "pipeline.inputPath": "입력 파일 경로",
    "pipeline.outputDir": "출력 폴더",
    "pipeline.templateName": "템플릿 이름",
    "pipeline.templatePath": "템플릿 경로",
    "pipeline.uploadFile": "업로드 파일",
    "pipeline.runPath": "Path 실행",
    "pipeline.runFile": "File 실행",
    "pipeline.idle": "대기 중",
    "pipeline.runningPath": "Path 실행 중...",
    "pipeline.runningFile": "업로드/실행 중...",
    "pipeline.success": "완료 (request_id={requestId})",
    "pipeline.failed": "실패",
    "metrics.title": "실행 메트릭",
    "metrics.subtitle": "최근 실행 요약",
    "metrics.artifacts": "아티팩트",
    "metrics.rows": "Rows",
    "metrics.columns": "Columns",
    "metrics.issues": "Issues",
    "metrics.requestId": "Request ID",
    "ops.title": "운영 인사이트",
    "ops.subtitle": "감사 이벤트 기반 운영 지표",
    "ops.range": "조회 기간",
    "ops.range6h": "최근 6시간",
    "ops.range24h": "최근 24시간",
    "ops.range7d": "최근 7일",
    "ops.rangeAll": "전체",
    "ops.statusFilter": "상태 필터",
    "ops.statusAll": "전체",
    "ops.statusSucceeded": "성공",
    "ops.statusFailed": "실패",
    "ops.statusStarted": "시작",
    "ops.eventType": "이벤트 타입",
    "ops.eventAll": "전체",
    "ops.eventAuth": "로그인",
    "ops.eventProcess": "처리",
    "ops.actor": "실행 주체 검색",
    "ops.actorPlaceholder": "예: local-admin",
    "ops.autoRefresh": "자동 새로고침",
    "ops.exportSummary": "서명 요약 ZIP 저장",
    "ops.exportAuditCsv": "서명 감사 ZIP 저장",
    "ops.exportHint": "내보내기 시 원본 파일과 서명 매니페스트(.sig.json)가 ZIP으로 생성됩니다.",
    "ops.successRate": "성공률",
    "ops.procSucceeded": "처리 성공",
    "ops.procFailed": "처리 실패",
    "ops.totalEvents": "총 이벤트",
    "ops.statusChart": "처리 상태 분포",
    "ops.throughputChart": "시간대별 처리량",
    "ops.topActors": "상위 실행 주체",
    "ops.anomalyNone": "이상징후 없음",
    "ops.anomalyTitle": "이상징후",
    "ops.flag.high_login_failure_24h": "최근 24시간 로그인 실패가 높습니다.",
    "ops.flag.high_process_failure_rate_24h": "최근 24시간 처리 실패율이 높습니다.",
    "ops.flag.consecutive_process_failures": "연속 처리 실패가 감지되었습니다.",
    "response.title": "응답 JSON",
    "response.subtitle": "API 원본 응답",
    "audit.title": "감사 이벤트",
    "audit.subtitle": "최근 인증/처리 로그",
    "audit.refresh": "새로고침",
    "readiness.title": "시스템 레디니스",
    "readiness.subtitle": "실행 전 핵심 구성요소 상태를 점검합니다.",
    "readiness.refresh": "점검",
    "readiness.idle": "대기 중",
    "readiness.healthy": "레디니스: 정상",
    "readiness.degraded": "레디니스: 주의 필요",
    "readiness.noData": "점검 데이터 없음",
    "readiness.status.ok": "정상",
    "readiness.status.failed": "실패",
    "readiness.status.skipped": "스킵",
    "readiness.check.specs": "스펙 로드",
    "readiness.check.audit_log_dir": "감사로그 저장소",
    "readiness.check.export_signing": "서명 설정",
    "readiness.check.llm_connectivity": "LLM 연결성",
    "verify.title": "서명 검증 센터",
    "verify.subtitle": "내보낸 원본 파일과 .sig.json 매니페스트 무결성을 검증합니다.",
    "verify.payload": "원본 파일",
    "verify.signature": "서명 매니페스트(.sig.json)",
    "verify.run": "검증 실행",
    "verify.idle": "대기 중",
    "verify.running": "검증 중...",
    "verify.valid": "검증 성공: 무결성/서명 일치",
    "verify.invalid": "검증 실패: 결과 JSON 확인 필요",
    "msg.none": "없음",
    "msg.noToken": "토큰: 없음",
    "msg.tokenActive": "토큰: 활성",
    "msg.noArtifacts": "아티팩트 없음",
    "msg.noAudit": "표시할 이벤트가 없습니다.",
    "msg.noActors": "표시할 실행 주체가 없습니다.",
    "msg.chartNoData": "데이터 없음",
    "toast.loginSuccess": "로그인 성공",
    "toast.loginFailed": "로그인 실패",
    "toast.logout": "로그아웃 되었습니다.",
    "toast.needLogin": "먼저 로그인하세요.",
    "toast.selectFile": "업로드 파일을 선택하세요.",
    "toast.pathDone": "Path 실행 완료",
    "toast.fileDone": "File 실행 완료",
    "toast.copyDone": "경로를 클립보드에 복사했습니다.",
    "toast.copyFail": "복사에 실패했습니다.",
    "toast.auditFail": "감사로그 조회 실패",
    "toast.summaryFail": "운영 요약 조회 실패",
    "toast.exportSummaryDone": "서명된 운영 요약 ZIP 저장 완료",
    "toast.exportAuditDone": "서명된 감사 ZIP 저장 완료",
    "toast.exportFail": "내보내기에 실패했습니다.",
    "toast.readinessFail": "레디니스 조회 실패",
    "toast.verifyValid": "서명 검증 성공",
    "toast.verifyInvalid": "서명 검증 실패",
    "toast.verifyFail": "서명 검증 요청 실패",
    "toast.verifySelect": "원본 파일과 서명 파일을 모두 선택하세요.",
    "toast.bootstrapRefreshed": "관리자 초기 설정 상태를 다시 확인했습니다.",
    "toast.serviceBriefFail": "서비스 브리프 조회 실패",
    "toast.reviewPackFail": "리뷰 패키지 조회 실패",
    "health.ok": "정상",
    "health.unavailable": "상태 확인 실패",
    "health.label": "상태",
    "health.authOn": "인증:on",
    "health.authOff": "인증:off",
    "health.signOn": "서명:on",
    "health.signOff": "서명:off",
    "action.copy": "복사",
    "errors.generic": "요청 처리 중 오류가 발생했습니다.",
  },
  en: {
    "app.eyebrow": "LOCAL SECURE AUTOMATION",
    "app.title": "Secure XL2HWP Studio",
    "app.tagline": "Air-gapped friendly studio from Excel cleanup to Hancom document automation",
    "serviceBrief.kicker": "Operator Contract",
    "serviceBrief.title": "Service Brief",
    "serviceBrief.subtitle": "Review the trust boundary, operator flow, and processing contract before running the pipeline.",
    "serviceBrief.loading": "Loading...",
    "serviceBrief.unavailable": "Service brief unavailable.",
    "serviceBrief.schema": "Process schema",
    "serviceBrief.authMode": "Auth mode",
    "serviceBrief.signing": "Signing mode",
    "serviceBrief.failedChecks": "Failed checks",
    "serviceBrief.roles": "Process roles",
    "serviceBrief.reviewFlow": "Review flow",
    "serviceBrief.twoMinuteReview": "2-minute review",
    "serviceBrief.trustBoundary": "Trust boundary",
    "serviceBrief.proofAssets": "Proof assets",
    "serviceBrief.watchouts": "Watchouts",
    "reviewPack.title": "Review pack",
    "reviewPack.approvalGate": "Approval gate",
    "reviewPack.proofBundle": "Proof bundle",
    "reviewPack.boundary": "Boundary",
    "reviewPack.artifacts": "Artifacts",
    "reviewPack.twoMinuteReview": "2-minute review",
    "reviewPack.sequence": "Review sequence",
    "reviewPack.proofAssets": "Proof assets",
    "control.language": "Language",
    "control.theme": "Theme",
    "control.brand": "Brand",
    "auth.title": "Authentication",
    "auth.subtitle": "JWT-based access control",
    "auth.userId": "User ID",
    "auth.password": "Password",
    "auth.login": "Sign In",
    "auth.logout": "Sign Out",
    "auth.currentUser": "Current user:",
    "auth.userPlaceholder": "local-admin",
    "auth.passwordPlaceholder": "StrongPassword!",
    "auth.bootstrapBadgeRequired": "Admin setup required",
    "auth.bootstrapBadgeReady": "Admin account ready",
    "auth.bootstrapTitle": "Create an admin ID first",
    "auth.bootstrapMessageRequired": "No active login account is configured yet. Follow these 3 steps to create a local admin first.",
    "auth.bootstrapMessageReady": "An active account is detected. You can sign in with your configured admin ID now.",
    "auth.bootstrapRefresh": "Recheck status",
    "auth.bootstrapStep1": "Set a strong AUTH_PASSWORD_PEPPER in .env.",
    "auth.bootstrapStep2": "Generate a password hash and register it in users.yaml.",
    "auth.bootstrapStep3": "Refresh the app and sign in with the admin account you created.",
    "auth.bootstrapRegistryLabel": "User registry file:",
    "auth.bootstrapHashLabel": "Hash command",
    "auth.bootstrapYamlLabel": "users.yaml sample",
    "pipeline.title": "Pipeline Run",
    "pipeline.subtitle": "Path mode / File upload mode",
    "pipeline.modePath": "Path Mode",
    "pipeline.modeFile": "File Mode",
    "pipeline.inputPath": "Input file path",
    "pipeline.outputDir": "Output directory",
    "pipeline.templateName": "Template name",
    "pipeline.templatePath": "Template path",
    "pipeline.uploadFile": "Upload file",
    "pipeline.runPath": "Run Path",
    "pipeline.runFile": "Run File",
    "pipeline.idle": "Idle",
    "pipeline.runningPath": "Running path pipeline...",
    "pipeline.runningFile": "Uploading and running...",
    "pipeline.success": "Done (request_id={requestId})",
    "pipeline.failed": "Failed",
    "metrics.title": "Execution Metrics",
    "metrics.subtitle": "Latest run snapshot",
    "metrics.artifacts": "Artifacts",
    "metrics.rows": "Rows",
    "metrics.columns": "Columns",
    "metrics.issues": "Issues",
    "metrics.requestId": "Request ID",
    "ops.title": "Operational Insights",
    "ops.subtitle": "Audit-event based operational telemetry",
    "ops.range": "Range",
    "ops.range6h": "Last 6 hours",
    "ops.range24h": "Last 24 hours",
    "ops.range7d": "Last 7 days",
    "ops.rangeAll": "All",
    "ops.statusFilter": "Status filter",
    "ops.statusAll": "All",
    "ops.statusSucceeded": "Succeeded",
    "ops.statusFailed": "Failed",
    "ops.statusStarted": "Started",
    "ops.eventType": "Event type",
    "ops.eventAll": "All",
    "ops.eventAuth": "Login",
    "ops.eventProcess": "Process",
    "ops.actor": "Actor contains",
    "ops.actorPlaceholder": "e.g. local-admin",
    "ops.autoRefresh": "Auto refresh",
    "ops.exportSummary": "Save Signed Summary ZIP",
    "ops.exportAuditCsv": "Save Signed Audit ZIP",
    "ops.exportHint": "Each export is a ZIP containing payload and signed .sig.json manifest.",
    "ops.successRate": "Success rate",
    "ops.procSucceeded": "Process succeeded",
    "ops.procFailed": "Process failed",
    "ops.totalEvents": "Total events",
    "ops.statusChart": "Process status distribution",
    "ops.throughputChart": "Hourly throughput",
    "ops.topActors": "Top actors",
    "ops.anomalyNone": "No anomalies",
    "ops.anomalyTitle": "Anomalies",
    "ops.flag.high_login_failure_24h": "High login failures in last 24h.",
    "ops.flag.high_process_failure_rate_24h": "High process failure rate in last 24h.",
    "ops.flag.consecutive_process_failures": "Consecutive process failures detected.",
    "response.title": "Response JSON",
    "response.subtitle": "Raw API payload",
    "audit.title": "Audit Events",
    "audit.subtitle": "Recent auth/process logs",
    "audit.refresh": "Refresh",
    "readiness.title": "System Readiness",
    "readiness.subtitle": "Checks critical runtime components before operation.",
    "readiness.refresh": "Run Check",
    "readiness.idle": "Idle",
    "readiness.healthy": "Readiness: healthy",
    "readiness.degraded": "Readiness: degraded",
    "readiness.noData": "No readiness data",
    "readiness.status.ok": "ok",
    "readiness.status.failed": "failed",
    "readiness.status.skipped": "skipped",
    "readiness.check.specs": "Spec loading",
    "readiness.check.audit_log_dir": "Audit storage",
    "readiness.check.export_signing": "Signing setup",
    "readiness.check.llm_connectivity": "LLM connectivity",
    "verify.title": "Signature Verify Center",
    "verify.subtitle": "Validate integrity using the exported payload and .sig.json manifest.",
    "verify.payload": "Payload file",
    "verify.signature": "Signature manifest (.sig.json)",
    "verify.run": "Run Verification",
    "verify.idle": "Idle",
    "verify.running": "Verifying...",
    "verify.valid": "Verification passed: hash/signature matched",
    "verify.invalid": "Verification failed: review result JSON",
    "msg.none": "None",
    "msg.noToken": "Token: none",
    "msg.tokenActive": "Token: active",
    "msg.noArtifacts": "No artifacts",
    "msg.noAudit": "No events to display.",
    "msg.noActors": "No actor data available.",
    "msg.chartNoData": "No data",
    "toast.loginSuccess": "Login successful",
    "toast.loginFailed": "Login failed",
    "toast.logout": "Signed out",
    "toast.needLogin": "Please login first.",
    "toast.selectFile": "Please choose a file to upload.",
    "toast.pathDone": "Path run complete",
    "toast.fileDone": "File run complete",
    "toast.copyDone": "Path copied to clipboard.",
    "toast.copyFail": "Copy failed.",
    "toast.auditFail": "Failed to fetch audit logs",
    "toast.summaryFail": "Failed to fetch ops summary",
    "toast.exportSummaryDone": "Saved signed summary ZIP package.",
    "toast.exportAuditDone": "Saved signed audit ZIP package.",
    "toast.exportFail": "Export failed.",
    "toast.readinessFail": "Failed to fetch readiness",
    "toast.verifyValid": "Signature verified successfully",
    "toast.verifyInvalid": "Signature verification failed",
    "toast.verifyFail": "Verification request failed",
    "toast.verifySelect": "Select both payload and signature files.",
    "toast.bootstrapRefreshed": "Admin bootstrap status refreshed.",
    "toast.serviceBriefFail": "Failed to fetch service brief",
    "toast.reviewPackFail": "Failed to fetch review pack",
    "health.ok": "OK",
    "health.unavailable": "Unavailable",
    "health.label": "Health",
    "health.authOn": "auth=on",
    "health.authOff": "auth=off",
    "health.signOn": "sign=on",
    "health.signOff": "sign=off",
    "action.copy": "Copy",
    "errors.generic": "Request failed.",
  },
};

const state = {
  token: localStorage.getItem("secure_xl2hwp_token") || "",
  user: null,
  mode: "path",
  authBootstrapRequired: Boolean(cfg.auth_bootstrap?.required),
  authUserTotal: Number(cfg.auth_bootstrap?.total_users || 0),
  authUserActive: Number(cfg.auth_bootstrap?.active_users || 0),
  authRegistryPath: cfg.auth_bootstrap?.registry_path || "specs/security/users.yaml",
  authBootstrapLoadError: Boolean(cfg.auth_bootstrap?.load_error),
  lang: localStorage.getItem("secure_ui_lang") || cfg.ui_defaults?.language || "ko",
  theme: localStorage.getItem("secure_ui_theme") || cfg.ui_defaults?.theme || "light",
  brand: localStorage.getItem("secure_ui_brand") || cfg.ui_defaults?.brand || "aqua",
  opsSinceHours: localStorage.getItem("secure_ops_since") || "24",
  opsStatus: localStorage.getItem("secure_ops_status") || "",
  opsEventType: localStorage.getItem("secure_ops_event_type") || "",
  opsActorContains: localStorage.getItem("secure_ops_actor_contains") || "",
  opsAutoRefresh: localStorage.getItem("secure_ops_auto") !== "false",
  lastResult: null,
  lastMetrics: {},
  lastArtifacts: {},
  lastAuditEvents: [],
  lastSummary: null,
  lastAnomalies: null,
  lastReadiness: null,
  lastServiceBrief: null,
  lastReviewPack: null,
  lastVerifyResult: null,
  verifyStatusKey: "verify.idle",
  verifyStatusTone: "neutral",
};

const els = {
  healthPill: document.getElementById("healthPill"),
  briefBadge: document.getElementById("briefBadge"),
  briefHeadline: document.getElementById("briefHeadline"),
  briefSchema: document.getElementById("briefSchema"),
  briefAuthMode: document.getElementById("briefAuthMode"),
  briefSigningMode: document.getElementById("briefSigningMode"),
  briefFailedChecks: document.getElementById("briefFailedChecks"),
  briefRoles: document.getElementById("briefRoles"),
  briefReviewFlow: document.getElementById("briefReviewFlow"),
  briefTwoMinuteReview: document.getElementById("briefTwoMinuteReview"),
  briefTrustBoundary: document.getElementById("briefTrustBoundary"),
  briefProofAssets: document.getElementById("briefProofAssets"),
  briefWatchouts: document.getElementById("briefWatchouts"),
  reviewPackHeadline: document.getElementById("reviewPackHeadline"),
  reviewPackGate: document.getElementById("reviewPackGate"),
  reviewPackProof: document.getElementById("reviewPackProof"),
  reviewPackBoundary: document.getElementById("reviewPackBoundary"),
  reviewPackArtifacts: document.getElementById("reviewPackArtifacts"),
  reviewPackTwoMinuteReview: document.getElementById("reviewPackTwoMinuteReview"),
  reviewPackSequence: document.getElementById("reviewPackSequence"),
  reviewPackProofAssets: document.getElementById("reviewPackProofAssets"),
  copyServiceBriefBtn: document.getElementById("copyServiceBriefBtn"),
  copyReviewPackBtn: document.getElementById("copyReviewPackBtn"),
  logoutBtn: document.getElementById("logoutBtn"),
  loginForm: document.getElementById("loginForm"),
  loginUserId: document.getElementById("loginUserId"),
  loginPassword: document.getElementById("loginPassword"),
  loginBtn: document.getElementById("loginBtn"),
  bootstrapCard: document.getElementById("bootstrapCard"),
  bootstrapBadge: document.getElementById("bootstrapBadge"),
  bootstrapMessage: document.getElementById("bootstrapMessage"),
  bootstrapRefreshBtn: document.getElementById("bootstrapRefreshBtn"),
  bootstrapRegistryPath: document.getElementById("bootstrapRegistryPath"),
  bootstrapHashCommand: document.getElementById("bootstrapHashCommand"),
  bootstrapYamlTemplate: document.getElementById("bootstrapYamlTemplate"),
  currentUserText: document.getElementById("currentUserText"),
  tokenStatus: document.getElementById("tokenStatus"),
  modePathBtn: document.getElementById("modePathBtn"),
  modeFileBtn: document.getElementById("modeFileBtn"),
  pathForm: document.getElementById("pathForm"),
  fileForm: document.getElementById("fileForm"),
  runStatus: document.getElementById("runStatus"),
  resultJson: document.getElementById("resultJson"),
  metricsGrid: document.getElementById("metricsGrid"),
  artifactsList: document.getElementById("artifactsList"),
  refreshAuditBtn: document.getElementById("refreshAuditBtn"),
  auditList: document.getElementById("auditList"),
  refreshReadinessBtn: document.getElementById("refreshReadinessBtn"),
  readinessOverall: document.getElementById("readinessOverall"),
  readinessList: document.getElementById("readinessList"),
  verifyForm: document.getElementById("verifyForm"),
  verifyPayloadFile: document.getElementById("verifyPayloadFile"),
  verifySignatureFile: document.getElementById("verifySignatureFile"),
  verifyRunBtn: document.getElementById("verifyRunBtn"),
  verifyStatus: document.getElementById("verifyStatus"),
  verifyResultJson: document.getElementById("verifyResultJson"),
  toast: document.getElementById("toast"),
  pathInputPath: document.getElementById("pathInputPath"),
  pathOutputDir: document.getElementById("pathOutputDir"),
  pathContract: document.getElementById("pathContract"),
  pathProfile: document.getElementById("pathProfile"),
  pathTemplateName: document.getElementById("pathTemplateName"),
  pathTemplatePath: document.getElementById("pathTemplatePath"),
  fileInput: document.getElementById("fileInput"),
  fileOutputDir: document.getElementById("fileOutputDir"),
  fileContract: document.getElementById("fileContract"),
  fileProfile: document.getElementById("fileProfile"),
  fileTemplateName: document.getElementById("fileTemplateName"),
  fileTemplatePath: document.getElementById("fileTemplatePath"),
  langSelect: document.getElementById("langSelect"),
  themeSelect: document.getElementById("themeSelect"),
  brandSelect: document.getElementById("brandSelect"),
  opsSinceSelect: document.getElementById("opsSinceSelect"),
  opsStatusSelect: document.getElementById("opsStatusSelect"),
  opsEventTypeSelect: document.getElementById("opsEventTypeSelect"),
  opsActorInput: document.getElementById("opsActorInput"),
  opsAutoRefresh: document.getElementById("opsAutoRefresh"),
  exportSummaryBtn: document.getElementById("exportSummaryBtn"),
  exportAuditCsvBtn: document.getElementById("exportAuditCsvBtn"),
  opsKpis: document.getElementById("opsKpis"),
  statusChartCanvas: document.getElementById("statusChartCanvas"),
  throughputChartCanvas: document.getElementById("throughputChartCanvas"),
  topActorsList: document.getElementById("topActorsList"),
  opsFlagsList: document.getElementById("opsFlagsList"),
};

function t(key) {
  const language = I18N[state.lang] ? state.lang : "ko";
  return I18N[language][key] || I18N.ko[key] || key;
}

function tf(key, params = {}) {
  let text = t(key);
  Object.entries(params).forEach(([name, value]) => {
    text = text.replaceAll(`{${name}}`, String(value));
  });
  return text;
}

function authHeaders() {
  if (!state.token) {
    return {};
  }
  return { Authorization: `Bearer ${state.token}` };
}

function setRevealAnimation() {
  const revealEls = document.querySelectorAll(".reveal");
  revealEls.forEach((el) => {
    const delay = Number(el.dataset.revealDelay || 0);
    el.style.setProperty("--reveal-delay", `${delay}ms`);
  });
}

function applyTheme() {
  document.documentElement.setAttribute("data-theme", state.theme);
  document.documentElement.setAttribute("data-brand", state.brand);
  localStorage.setItem("secure_ui_theme", state.theme);
  localStorage.setItem("secure_ui_brand", state.brand);
}

function applyI18n() {
  document.documentElement.lang = state.lang;
  localStorage.setItem("secure_ui_lang", state.lang);

  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.dataset.i18n;
    if (key) {
      el.textContent = t(key);
    }
  });

  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = el.dataset.i18nPlaceholder;
    if (key) {
      el.placeholder = t(key);
    }
  });

  renderBootstrapGuide();
  setAuthState();
  renderMetrics(state.lastMetrics);
  renderArtifacts(state.lastArtifacts);
  renderAudit(state.lastAuditEvents);
  renderOpsSummary(state.lastSummary, state.lastAnomalies);
  renderReadiness(state.lastReadiness);
  renderServiceBrief(state.lastServiceBrief);
  renderVerifyResult(state.lastVerifyResult);
  setVerifyStatus(state.verifyStatusKey, state.verifyStatusTone);
  refreshHealth().catch(() => {});
}

function safeSelectValue(selectEl, candidate, fallback = "") {
  const options = Array.from(selectEl.options).map((opt) => opt.value);
  if (options.includes(candidate)) {
    return candidate;
  }
  return fallback;
}

function bootstrapRegistryPath() {
  return state.authRegistryPath || "specs/security/users.yaml";
}

function bootstrapHashCommand() {
  return "python scripts/hash_password.py --password 'StrongPassword!' --pepper 'YOUR_AUTH_PASSWORD_PEPPER'";
}

function bootstrapYamlTemplate() {
  return `users:
  - user_id: "local-admin"
    role: "Admin"
    password_hash: "PASTE_HASH_HERE"
    active: true`;
}

function renderBootstrapGuide() {
  if (!els.bootstrapCard) {
    return;
  }

  if (cfg.auth_enabled === false) {
    els.bootstrapCard.classList.add("hidden");
    return;
  }

  els.bootstrapCard.classList.remove("hidden");

  const required = Boolean(state.authBootstrapRequired);
  els.bootstrapCard.classList.toggle("ready", !required);
  if (els.bootstrapBadge) {
    els.bootstrapBadge.classList.toggle("ready", !required);
    els.bootstrapBadge.textContent = required ? t("auth.bootstrapBadgeRequired") : t("auth.bootstrapBadgeReady");
  }
  if (els.bootstrapMessage) {
    els.bootstrapMessage.textContent = required
      ? t("auth.bootstrapMessageRequired")
      : t("auth.bootstrapMessageReady");
  }
  if (els.bootstrapRegistryPath) {
    els.bootstrapRegistryPath.textContent = bootstrapRegistryPath();
  }
  if (els.bootstrapHashCommand) {
    els.bootstrapHashCommand.textContent = bootstrapHashCommand();
  }
  if (els.bootstrapYamlTemplate) {
    els.bootstrapYamlTemplate.textContent = bootstrapYamlTemplate();
  }
}

function initDefaults() {
  const defaults = cfg.default_paths || {};

  const inputPath = defaults.input_path || "examples/input/sample_projects.xlsx";
  const outputDir = defaults.output_dir || "examples/output";
  const contractName = defaults.contract_name || "default";
  const profileName = defaults.profile_name || "default";
  const templateName = defaults.template_name || "default";
  const templatePath = defaults.template_path || "examples/input/sample_report_template.txt";

  els.pathInputPath.value = inputPath;
  els.pathOutputDir.value = outputDir;
  els.pathContract.value = contractName;
  els.pathProfile.value = profileName;
  els.pathTemplateName.value = templateName;
  els.pathTemplatePath.value = templatePath;

  els.fileOutputDir.value = outputDir;
  els.fileContract.value = contractName;
  els.fileProfile.value = profileName;
  els.fileTemplateName.value = templateName;
  els.fileTemplatePath.value = templatePath;

  els.loginUserId.value = "local-admin";
  els.loginPassword.value = "";

  els.langSelect.value = state.lang;
  els.themeSelect.value = state.theme;
  els.brandSelect.value = state.brand;
  state.opsSinceHours = safeSelectValue(els.opsSinceSelect, state.opsSinceHours, "24");
  state.opsStatus = safeSelectValue(els.opsStatusSelect, state.opsStatus, "");
  state.opsEventType = safeSelectValue(els.opsEventTypeSelect, state.opsEventType, "");
  els.opsSinceSelect.value = state.opsSinceHours;
  els.opsStatusSelect.value = state.opsStatus;
  els.opsEventTypeSelect.value = state.opsEventType;
  els.opsActorInput.value = state.opsActorContains;
  els.opsAutoRefresh.checked = state.opsAutoRefresh;

  localStorage.setItem("secure_ops_since", state.opsSinceHours);
  localStorage.setItem("secure_ops_status", state.opsStatus);
  localStorage.setItem("secure_ops_event_type", state.opsEventType);
  localStorage.setItem("secure_ops_actor_contains", state.opsActorContains);
  renderBootstrapGuide();
}

function toggleMode(mode) {
  state.mode = mode;
  const isPath = mode === "path";

  els.modePathBtn.classList.toggle("active", isPath);
  els.modeFileBtn.classList.toggle("active", !isPath);
  els.pathForm.classList.toggle("hidden", !isPath);
  els.fileForm.classList.toggle("hidden", isPath);
}

function showToast(message, isError = false) {
  els.toast.textContent = message;
  els.toast.style.background = isError
    ? "#8b2f12"
    : getComputedStyle(document.documentElement).getPropertyValue("--toast-bg");
  els.toast.classList.remove("hidden");
  window.setTimeout(() => {
    els.toast.classList.add("hidden");
  }, 2300);
}

function safeErrorMessage(payload, fallbackKey = "errors.generic") {
  if (!payload || !payload.detail) {
    return t(fallbackKey);
  }

  const detail = payload.detail;
  if (typeof detail === "string") {
    return detail;
  }

  if (typeof detail.message === "string") {
    const rid = detail.request_id ? ` (request_id: ${detail.request_id})` : "";
    const retrySuffix =
      typeof detail.retry_after_seconds === "number"
        ? ` (retry_after=${detail.retry_after_seconds}s)`
        : "";
    return `${detail.message}${retrySuffix}${rid}`;
  }

  return t(fallbackKey);
}

async function fetchJSON(url, options = {}) {
  const res = await fetch(url, options);
  let data = null;
  try {
    data = await res.json();
  } catch (_err) {
    data = null;
  }

  if (!res.ok) {
    const err = new Error("request_failed");
    err.status = res.status;
    err.payload = data;
    err.requestId = res.headers.get("x-request-id");
    throw err;
  }

  return { data, res };
}

async function fetchBlob(url, options = {}) {
  const res = await fetch(url, options);
  const blob = await res.blob();

  if (!res.ok) {
    const err = new Error("request_failed");
    err.status = res.status;
    err.requestId = res.headers.get("x-request-id");

    try {
      const text = await blob.text();
      err.payload = JSON.parse(text);
    } catch (_err) {
      err.payload = { detail: "request_failed" };
    }
    throw err;
  }

  return { blob, res };
}

function setAuthState() {
  const hasToken = Boolean(state.token);
  els.logoutBtn.disabled = !hasToken;
  els.loginBtn.disabled = hasToken;

  if (hasToken) {
    els.tokenStatus.textContent = t("msg.tokenActive");
    return;
  }

  els.currentUserText.textContent = t("msg.none");
  els.tokenStatus.textContent = t("msg.noToken");
}

function setVerifyStatus(key, tone = "neutral") {
  state.verifyStatusKey = key;
  state.verifyStatusTone = tone;

  els.verifyStatus.classList.remove("ok", "warn");
  if (tone === "ok" || tone === "warn") {
    els.verifyStatus.classList.add(tone);
  }
  els.verifyStatus.textContent = t(key);
}

function renderVerifyResult(payload) {
  state.lastVerifyResult = payload || null;
  els.verifyResultJson.textContent = JSON.stringify(payload ?? {}, null, 2);
}

function renderMetrics(metrics = {}) {
  state.lastMetrics = metrics || {};

  const cards = [
    { label: t("metrics.rows"), value: metrics.row_count ?? "-" },
    { label: t("metrics.columns"), value: metrics.column_count ?? "-" },
    { label: t("metrics.issues"), value: metrics.issue_count ?? "-" },
    { label: t("metrics.requestId"), value: metrics.request_id || "-" },
  ];

  els.metricsGrid.innerHTML = cards
    .map(
      (item) => `
      <article class="metric-card">
        <span>${item.label}</span>
        <strong>${item.value}</strong>
      </article>
    `
    )
    .join("");
}

function renderArtifacts(artifacts = {}) {
  state.lastArtifacts = artifacts || {};

  const entries = Object.entries(artifacts || {});
  if (!entries.length) {
    els.artifactsList.innerHTML = `<li class="artifact-item">${t("msg.noArtifacts")}</li>`;
    return;
  }

  els.artifactsList.innerHTML = "";
  entries.forEach(([name, value]) => {
    const item = document.createElement("li");
    item.className = "artifact-item";

    const left = document.createElement("div");
    left.innerHTML = `<strong>${name}</strong><div class="artifact-path">${value}</div>`;

    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "ghost-btn";
    copyBtn.textContent = t("action.copy");
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(String(value));
        showToast(t("toast.copyDone"));
      } catch (_err) {
        showToast(t("toast.copyFail"), true);
      }
    });

    item.appendChild(left);
    item.appendChild(copyBtn);
    els.artifactsList.appendChild(item);
  });
}

function renderResultJson(payload) {
  state.lastResult = payload;
  els.resultJson.textContent = JSON.stringify(payload ?? {}, null, 2);
}

function renderAudit(events = []) {
  state.lastAuditEvents = events || [];

  if (!events || !events.length) {
    els.auditList.innerHTML = `<li class="audit-item">${t("msg.noAudit")}</li>`;
    return;
  }

  els.auditList.innerHTML = "";
  events.forEach((event) => {
    const item = document.createElement("li");
    item.className = "audit-item";

    const status = String(event.status || "unknown");
    const actor = event.actor || {};
    const detail = event.details || {};
    const summary =
      detail.reason ||
      detail.error ||
      `row_count=${detail.row_count ?? "-"}, issue_count=${detail.issue_count ?? "-"}`;

    item.innerHTML = `
      <div class="audit-top">
        <span class="audit-type">${event.event_type || "event"}</span>
        <span class="audit-status ${status}">${status}</span>
      </div>
      <div class="muted">${event.timestamp_utc || "-"} | ${actor.user_id || "unknown"} (${actor.role || "unknown"})</div>
      <div class="artifact-path">${summary}</div>
    `;
    els.auditList.appendChild(item);
  });
}

function readinessCheckLabel(name) {
  const key = `readiness.check.${name}`;
  const translated = t(key);
  return translated === key ? String(name || "check") : translated;
}

function readinessStatusLabel(status) {
  return t(`readiness.status.${status}`);
}

function readinessTone(status) {
  if (status === "ok") {
    return "ok";
  }
  if (status === "failed") {
    return "warn";
  }
  return "neutral";
}

function renderReadiness(payload = null) {
  state.lastReadiness = payload || null;

  els.readinessOverall.classList.remove("ok", "warn", "neutral");

  if (!payload || !Array.isArray(payload.checks)) {
    els.readinessOverall.classList.add("neutral");
    els.readinessOverall.textContent = t("readiness.idle");
    els.readinessList.innerHTML = `<li class="artifact-item">${t("readiness.noData")}</li>`;
    return;
  }

  const isHealthy = payload.overall_status === "healthy";
  els.readinessOverall.classList.add(isHealthy ? "ok" : "warn");
  els.readinessOverall.textContent = isHealthy ? t("readiness.healthy") : t("readiness.degraded");

  if (!payload.checks.length) {
    els.readinessList.innerHTML = `<li class="artifact-item">${t("readiness.noData")}</li>`;
    return;
  }

  els.readinessList.innerHTML = "";
  payload.checks.forEach((check) => {
    const status = String(check.status || "skipped");
    const tone = readinessTone(status);
    const item = document.createElement("li");
    item.className = "artifact-item";
    item.innerHTML = `
      <div>
        <strong>${readinessCheckLabel(check.name || "unknown")}</strong>
        <div class="artifact-path">${check.detail || "-"}</div>
      </div>
      <span class="readiness-badge ${tone}">${readinessStatusLabel(status)}</span>
    `;
    els.readinessList.appendChild(item);
  });
}

function renderBriefList(container, items) {
  container.innerHTML = "";
  if (!items || !items.length) {
    container.innerHTML = `<li class="artifact-item">${t("msg.none")}</li>`;
    return;
  }

  items.forEach((item) => {
    const li = document.createElement("li");
    li.className = "artifact-item";
    li.innerHTML = `<span>${item}</span>`;
    container.appendChild(li);
  });
}

async function copyTextValue(value) {
  try {
    await navigator.clipboard.writeText(String(value || ""));
    showToast(t("toast.copyDone"));
    return true;
  } catch (_err) {
    showToast(t("toast.copyFail"), true);
    return false;
  }
}

function formatProofAssets(items) {
  return (items || []).map((item) => {
    const label = item?.label || "Asset";
    const path = item?.path || "";
    const why = item?.why || "";
    const kind = item?.kind ? `[${item.kind}] ` : "";
    return why ? `${kind}${label} -> ${path} :: ${why}` : `${kind}${label} -> ${path}`;
  });
}

function renderServiceBrief(payload = null) {
  state.lastServiceBrief = payload || null;

  if (!payload) {
    els.briefBadge.classList.remove("ok", "warn");
    els.briefBadge.classList.add("neutral");
    els.briefBadge.textContent = t("serviceBrief.unavailable");
    els.briefHeadline.textContent = t("serviceBrief.unavailable");
    els.briefSchema.textContent = "-";
    els.briefAuthMode.textContent = "-";
    els.briefSigningMode.textContent = "-";
    els.briefFailedChecks.textContent = "-";
    renderBriefList(els.briefRoles, []);
    renderBriefList(els.briefReviewFlow, []);
    renderBriefList(els.briefTwoMinuteReview, []);
    renderBriefList(els.briefTrustBoundary, []);
    renderBriefList(els.briefProofAssets, []);
    renderBriefList(els.briefWatchouts, []);
    return;
  }

  const ok = payload.status === "ok";
  const failedChecks = Array.isArray(payload.readiness?.failed_checks)
    ? payload.readiness.failed_checks.length
    : payload.evidence_counts?.readiness_failed_checks || 0;

  els.briefBadge.classList.remove("neutral", "ok", "warn");
  els.briefBadge.classList.add(ok ? "ok" : "warn");
  els.briefBadge.textContent = ok ? t("readiness.healthy") : t("readiness.degraded");
  els.briefHeadline.textContent = payload.headline || t("serviceBrief.unavailable");
  els.briefSchema.textContent = payload.report_contract?.schema || "-";
  els.briefAuthMode.textContent = payload.auth_mode || "-";
  els.briefSigningMode.textContent = payload.signing_mode || "-";
  els.briefFailedChecks.textContent = String(failedChecks);
  renderBriefList(els.briefRoles, payload.allowed_process_roles || []);
  renderBriefList(els.briefReviewFlow, payload.review_flow || []);
  renderBriefList(els.briefTwoMinuteReview, payload.two_minute_review || []);
  renderBriefList(els.briefTrustBoundary, payload.trust_boundary || []);
  renderBriefList(els.briefProofAssets, formatProofAssets(payload.proof_assets || []));
  renderBriefList(els.briefWatchouts, payload.watchouts || []);
}

function renderReviewPack(payload = null) {
  state.lastReviewPack = payload || null;

  if (!payload) {
    els.reviewPackHeadline.textContent = t("serviceBrief.unavailable");
    els.reviewPackGate.textContent = "-";
    els.reviewPackProof.textContent = "-";
    els.reviewPackBoundary.textContent = "-";
    renderBriefList(els.reviewPackArtifacts, []);
    renderBriefList(els.reviewPackTwoMinuteReview, []);
    renderBriefList(els.reviewPackSequence, []);
    renderBriefList(els.reviewPackProofAssets, []);
    return;
  }

  const proofBundle = payload.proof_bundle || {};
  const approvalGate = payload.approval_gate || {};
  const targetBoundary = payload.target_boundary || {};
  const failedChecks = Number(proofBundle.readiness_failed_checks || 0);
  const gateText = approvalGate.auth_bootstrap_required
    ? "bootstrap required"
    : `${(approvalGate.process_roles || []).length || 0} process roles ready`;

  els.reviewPackHeadline.textContent = payload.headline || "-";
  els.reviewPackGate.textContent = gateText;
  els.reviewPackProof.textContent = `${proofBundle.signed_export_mode || "unknown"} / ${failedChecks} failed checks`;
  els.reviewPackBoundary.textContent = targetBoundary.output_base_dir || "-";
  renderBriefList(els.reviewPackArtifacts, payload.artifacts || []);
  renderBriefList(els.reviewPackTwoMinuteReview, payload.two_minute_review || []);
  renderBriefList(els.reviewPackSequence, payload.review_sequence || []);
  renderBriefList(els.reviewPackProofAssets, formatProofAssets(payload.proof_assets || []));
}

function drawEmpty(canvas, label) {
  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(220, Math.floor(canvas.clientWidth * ratio));
  const height = Math.max(160, Math.floor(canvas.clientHeight * ratio));
  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--muted").trim();
  ctx.font = `${12 * ratio}px "IBM Plex Sans KR"`;
  ctx.textAlign = "center";
  ctx.fillText(label, width / 2, height / 2);
}

function drawDonut(canvas, segments) {
  const total = segments.reduce((sum, seg) => sum + seg.value, 0);
  if (!total) {
    drawEmpty(canvas, t("msg.chartNoData"));
    return;
  }

  const style = getComputedStyle(document.documentElement);
  const palette = [
    style.getPropertyValue("--accent").trim(),
    style.getPropertyValue("--warn").trim(),
    style.getPropertyValue("--sun").trim(),
    "#8aa6bf",
  ];

  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(230, Math.floor(canvas.clientWidth * ratio));
  const height = Math.max(170, Math.floor(canvas.clientHeight * ratio));
  canvas.width = width;
  canvas.height = height;

  const cx = width * 0.35;
  const cy = height * 0.5;
  const radius = Math.min(width, height) * 0.28;

  ctx.clearRect(0, 0, width, height);

  let startAngle = -Math.PI / 2;
  segments.forEach((segment, index) => {
    const slice = (segment.value / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.arc(cx, cy, radius, startAngle, startAngle + slice);
    ctx.closePath();
    ctx.fillStyle = palette[index % palette.length];
    ctx.fill();
    startAngle += slice;
  });

  ctx.beginPath();
  ctx.arc(cx, cy, radius * 0.56, 0, Math.PI * 2);
  ctx.fillStyle = style.getPropertyValue("--surface-strong").trim();
  ctx.fill();

  ctx.fillStyle = style.getPropertyValue("--text").trim();
  ctx.font = `${11 * ratio}px "Space Grotesk"`;
  ctx.textAlign = "center";
  ctx.fillText(String(total), cx, cy + 4);

  const legendX = width * 0.6;
  const legendTop = height * 0.24;
  segments.forEach((segment, index) => {
    const y = legendTop + index * 20 * ratio;
    ctx.fillStyle = palette[index % palette.length];
    ctx.fillRect(legendX, y - 8 * ratio, 10 * ratio, 10 * ratio);

    ctx.fillStyle = style.getPropertyValue("--muted").trim();
    ctx.font = `${9.5 * ratio}px "IBM Plex Sans KR"`;
    ctx.textAlign = "left";
    ctx.fillText(`${segment.label}: ${segment.value}`, legendX + 14 * ratio, y);
  });
}

function drawBars(canvas, labels, values) {
  const total = values.reduce((acc, v) => acc + v, 0);
  if (!total || !labels.length) {
    drawEmpty(canvas, t("msg.chartNoData"));
    return;
  }

  const style = getComputedStyle(document.documentElement);
  const accent = style.getPropertyValue("--accent").trim();
  const textColor = style.getPropertyValue("--muted").trim();
  const lineColor = style.getPropertyValue("--line").trim();

  const ctx = canvas.getContext("2d");
  const ratio = window.devicePixelRatio || 1;
  const width = Math.max(260, Math.floor(canvas.clientWidth * ratio));
  const height = Math.max(170, Math.floor(canvas.clientHeight * ratio));
  canvas.width = width;
  canvas.height = height;

  ctx.clearRect(0, 0, width, height);

  const paddingX = 22 * ratio;
  const paddingY = 18 * ratio;
  const chartW = width - paddingX * 2;
  const chartH = height - paddingY * 2;
  const maxValue = Math.max(...values, 1);

  ctx.strokeStyle = lineColor;
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(paddingX, height - paddingY);
  ctx.lineTo(width - paddingX, height - paddingY);
  ctx.stroke();

  const barCount = labels.length;
  const slotW = chartW / barCount;
  const barW = Math.max(8 * ratio, slotW * 0.55);

  values.forEach((value, idx) => {
    const x = paddingX + slotW * idx + (slotW - barW) / 2;
    const barH = (value / maxValue) * (chartH - 18 * ratio);
    const y = height - paddingY - barH;

    ctx.fillStyle = accent;
    ctx.fillRect(x, y, barW, barH);

    if (idx % Math.ceil(barCount / 6) === 0 || idx === barCount - 1) {
      const label = labels[idx];
      ctx.fillStyle = textColor;
      ctx.font = `${8.5 * ratio}px "IBM Plex Sans KR"`;
      ctx.textAlign = "center";
      ctx.fillText(label, x + barW / 2, height - 4 * ratio);
    }
  });
}

function renderTopActors(topActors) {
  if (!topActors || !topActors.length) {
    els.topActorsList.innerHTML = `<li class="artifact-item">${t("msg.noActors")}</li>`;
    return;
  }

  els.topActorsList.innerHTML = "";
  topActors.forEach((row) => {
    const item = document.createElement("li");
    item.className = "artifact-item";
    item.innerHTML = `<strong>${row.actor}</strong><span>${row.count}</span>`;
    els.topActorsList.appendChild(item);
  });
}

function anomalyLabel(flag) {
  return t(`ops.flag.${flag}`);
}

function renderAnomalies(anomalies) {
  state.lastAnomalies = anomalies || null;

  if (!anomalies || !Array.isArray(anomalies.flags) || anomalies.flags.length === 0) {
    els.opsFlagsList.innerHTML = `<li class="artifact-item">${t("ops.anomalyNone")}</li>`;
    return;
  }

  els.opsFlagsList.innerHTML = "";
  anomalies.flags.forEach((flag) => {
    const item = document.createElement("li");
    item.className = "artifact-item anomaly-item";
    item.innerHTML = `<strong>${t("ops.anomalyTitle")}</strong><span>${anomalyLabel(flag)}</span>`;
    els.opsFlagsList.appendChild(item);
  });
}

function renderOpsSummary(summary, anomalies = null) {
  state.lastSummary = summary || null;
  state.lastAnomalies = anomalies || null;

  const empty = {
    process_success_rate: null,
    process_status_counts: {},
    total_events: 0,
    top_actors: [],
    process_hourly: [],
  };
  const view = summary || empty;

  const succeeded = view.process_status_counts?.succeeded || 0;
  const failed = view.process_status_counts?.failed || 0;
  const totalEvents = view.total_events || 0;
  const successRate = view.process_success_rate == null ? "-" : `${view.process_success_rate}%`;

  const cards = [
    { label: t("ops.successRate"), value: successRate },
    { label: t("ops.procSucceeded"), value: succeeded },
    { label: t("ops.procFailed"), value: failed },
    { label: t("ops.totalEvents"), value: totalEvents },
  ];

  els.opsKpis.innerHTML = cards
    .map(
      (item) => `
      <article class="metric-card">
        <span>${item.label}</span>
        <strong>${item.value}</strong>
      </article>
    `
    )
    .join("");

  drawDonut(els.statusChartCanvas, [
    { label: t("ops.statusSucceeded"), value: succeeded },
    { label: t("ops.statusFailed"), value: failed },
    { label: t("ops.statusStarted"), value: view.process_status_counts?.started || 0 },
  ]);

  const hourly = view.process_hourly || [];
  drawBars(
    els.throughputChartCanvas,
    hourly.map((x) => x.bucket),
    hourly.map((x) => x.count)
  );

  renderTopActors(view.top_actors || []);
  renderAnomalies(anomalies);
}

function currentFileStamp() {
  return new Date().toISOString().replace(/[:.]/g, "-");
}

function sanitizeFileToken(value, fallback = "all") {
  const cleaned = String(value || "")
    .trim()
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "");
  return cleaned || fallback;
}

function exportFilterSuffix() {
  const parts = [
    sanitizeFileToken(state.opsSinceHours || "all", "all"),
    sanitizeFileToken(state.opsStatus || "all", "all"),
    sanitizeFileToken(state.opsEventType || "all", "all"),
    sanitizeFileToken(state.opsActorContains || "all", "all"),
  ];
  return parts.join("_");
}

function downloadBlobFile(filename, blob) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

function fileNameFromDisposition(contentDisposition, fallbackName) {
  if (!contentDisposition) {
    return fallbackName;
  }
  const match = contentDisposition.match(/filename=\"?([^\";]+)\"?/i);
  if (!match || !match[1]) {
    return fallbackName;
  }
  return match[1];
}

async function exportOpsSummaryJson() {
  if (!state.token && cfg.auth_enabled !== false) {
    showToast(t("toast.needLogin"), true);
    return;
  }

  try {
    const query = buildOpsQuery(500);
    const endpoint = "/ops/audit/export/summary.bundle.zip";
    const { blob, res } = await fetchBlob(`${endpoint}?${query}`, {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
    });
    const fallback = `audit-summary-${exportFilterSuffix()}-${currentFileStamp()}.bundle.zip`;
    const filename = fileNameFromDisposition(res.headers.get("content-disposition"), fallback);
    downloadBlobFile(filename, blob);
    showToast(t("toast.exportSummaryDone"));
  } catch (_err) {
    showToast(t("toast.exportFail"), true);
  }
}

async function copyServiceBriefSnapshot() {
  const payload = state.lastServiceBrief || {};
  const lines = [
    "secure-xl2hwp-local service brief",
    `Headline: ${payload.headline || els.briefHeadline.textContent || "-"}`,
    `Schema: ${payload.report_contract?.schema || els.briefSchema.textContent || "-"}`,
    `Auth: ${payload.auth_mode || els.briefAuthMode.textContent || "-"}`,
    `Signing: ${payload.signing_mode || els.briefSigningMode.textContent || "-"}`,
    "",
    "2-minute review",
    ...((payload.two_minute_review || []).map((item) => `- ${item}`)),
  ];
  await copyTextValue(lines.join("\n"));
}

async function copyReviewPackSnapshot() {
  const payload = state.lastReviewPack || {};
  const lines = [
    "secure-xl2hwp-local review pack",
    `Headline: ${payload.headline || els.reviewPackHeadline.textContent || "-"}`,
    `Gate: ${els.reviewPackGate.textContent || "-"}`,
    `Proof: ${els.reviewPackProof.textContent || "-"}`,
    `Boundary: ${els.reviewPackBoundary.textContent || "-"}`,
    "",
    "Review sequence",
    ...((payload.review_sequence || []).map((item) => `- ${item}`)),
    "",
    "Proof assets",
    ...formatProofAssets(payload.proof_assets || []).map((item) => `- ${item}`),
  ];
  await copyTextValue(lines.join("\n"));
}

async function exportAuditCsv() {
  if (!state.token && cfg.auth_enabled !== false) {
    showToast(t("toast.needLogin"), true);
    return;
  }

  try {
    const query = buildOpsQuery(200);
    const endpoint = "/ops/audit/export/recent.bundle.zip";
    const { blob, res } = await fetchBlob(`${endpoint}?${query}`, {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
    });
    const fallback = `audit-recent-${exportFilterSuffix()}-${currentFileStamp()}.bundle.zip`;
    const filename = fileNameFromDisposition(res.headers.get("content-disposition"), fallback);
    downloadBlobFile(filename, blob);
    showToast(t("toast.exportAuditDone"));
  } catch (_err) {
    showToast(t("toast.exportFail"), true);
  }
}

async function verifyExportSignature(event) {
  event.preventDefault();

  if (!state.token && cfg.auth_enabled !== false) {
    showToast(t("toast.needLogin"), true);
    return;
  }

  const payload = els.verifyPayloadFile.files?.[0];
  const signature = els.verifySignatureFile.files?.[0];
  if (!payload || !signature) {
    showToast(t("toast.verifySelect"), true);
    return;
  }

  setVerifyStatus("verify.running", "neutral");

  const formData = new FormData();
  formData.append("payload_file", payload);
  formData.append("signature_file", signature);

  try {
    const { data } = await fetchJSON("/ops/audit/export/verify", {
      method: "POST",
      headers: {
        ...authHeaders(),
      },
      body: formData,
    });
    renderVerifyResult(data);
    if (data?.overall_valid) {
      setVerifyStatus("verify.valid", "ok");
      showToast(t("toast.verifyValid"));
      return;
    }
    setVerifyStatus("verify.invalid", "warn");
    showToast(t("toast.verifyInvalid"), true);
  } catch (err) {
    setVerifyStatus("verify.invalid", "warn");
    showToast(safeErrorMessage(err.payload, "toast.verifyFail"), true);
  }
}

function buildOpsQuery(baseLimit) {
  const params = new URLSearchParams();
  params.set("limit", String(baseLimit));

  if (state.opsSinceHours) {
    params.set("since_hours", state.opsSinceHours);
  }
  if (state.opsStatus) {
    params.set("status", state.opsStatus);
  }
  if (state.opsEventType) {
    params.set("event_type", state.opsEventType);
  }
  if (state.opsActorContains.trim()) {
    params.set("actor_contains", state.opsActorContains.trim());
  }

  return params.toString();
}

async function refreshHealth() {
  try {
    const { data } = await fetchJSON("/health", { method: "GET" });
    const ok = data?.status === "ok";
    const bootstrap = data?.auth_bootstrap || {};
    state.authBootstrapRequired = Boolean(
      data?.auth_bootstrap_required ?? bootstrap.required ?? state.authBootstrapRequired
    );
    state.authUserTotal = Number(bootstrap.total_users ?? state.authUserTotal ?? 0);
    state.authUserActive = Number(bootstrap.active_users ?? state.authUserActive ?? 0);
    state.authRegistryPath = bootstrap.registry_path || state.authRegistryPath || "specs/security/users.yaml";
    state.authBootstrapLoadError = Boolean(bootstrap.load_error);
    renderBootstrapGuide();

    els.healthPill.classList.remove("neutral", "warn", "ok");
    els.healthPill.classList.add(ok ? "ok" : "warn");
    const authState = data.auth_enabled ? t("health.authOn") : t("health.authOff");
    const signingState = data.export_signing_enabled ? t("health.signOn") : t("health.signOff");
    els.healthPill.textContent = `${t("health.label")}: ${ok ? t("health.ok") : data.status} | ${authState} | ${signingState}`;
  } catch (_err) {
    els.healthPill.classList.remove("neutral", "ok");
    els.healthPill.classList.add("warn");
    els.healthPill.textContent = `${t("health.label")}: ${t("health.unavailable")}`;
  }
}

async function refreshServiceBrief() {
  try {
    const { data } = await fetchJSON("/ops/service-brief", { method: "GET" });
    renderServiceBrief(data || null);
  } catch (_err) {
    renderServiceBrief(null);
  }
}

async function refreshReviewPack() {
  try {
    const { data } = await fetchJSON("/ops/review-pack", { method: "GET" });
    renderReviewPack(data || null);
  } catch (_err) {
    renderReviewPack(null);
  }
}

async function refreshMe() {
  if (!state.token) {
    setAuthState();
    return;
  }

  try {
    const { data } = await fetchJSON("/auth/me", {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
    });
    state.user = data;
    els.currentUserText.textContent = `${data.user_id} (${data.role})`;
    setAuthState();
  } catch (_err) {
    state.token = "";
    state.user = null;
    localStorage.removeItem("secure_xl2hwp_token");
    setAuthState();
  }
}

async function login(event) {
  event.preventDefault();

  try {
    const { data } = await fetchJSON("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: els.loginUserId.value.trim(),
        password: els.loginPassword.value,
      }),
    });

    state.token = data.access_token;
    localStorage.setItem("secure_xl2hwp_token", state.token);
    await refreshMe();
    await refreshAudit();
    await refreshOpsSummary();
    showToast(t("toast.loginSuccess"));
  } catch (err) {
    showToast(safeErrorMessage(err.payload, "toast.loginFailed"), true);
  }
}

function logout() {
  state.token = "";
  state.user = null;
  localStorage.removeItem("secure_xl2hwp_token");
  setAuthState();
  renderAudit([]);
  renderOpsSummary(null, null);
  renderReadiness(null);
  renderVerifyResult(null);
  setVerifyStatus("verify.idle", "neutral");
  showToast(t("toast.logout"));
}

async function runPath(event) {
  event.preventDefault();

  if (!state.token && cfg.auth_enabled !== false) {
    showToast(t("toast.needLogin"), true);
    return;
  }

  const payload = {
    input_path: els.pathInputPath.value.trim(),
    output_dir: els.pathOutputDir.value.trim(),
    contract_name: els.pathContract.value.trim(),
    profile_name: els.pathProfile.value.trim(),
    template_name: els.pathTemplateName.value.trim(),
    template_path: els.pathTemplatePath.value.trim(),
  };

  els.runStatus.textContent = t("pipeline.runningPath");
  try {
    const { data, res } = await fetchJSON("/process/path", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders(),
      },
      body: JSON.stringify(payload),
    });

    const requestId = res.headers.get("x-request-id") || "-";
    const metrics = data?.outcome?.metrics || {};
    metrics.request_id = requestId;

    renderResultJson(data);
    renderMetrics(metrics);
    renderArtifacts(data?.outcome?.artifacts || {});
    await refreshAudit();
    await refreshOpsSummary();
    els.runStatus.textContent = tf("pipeline.success", { requestId });
    showToast(t("toast.pathDone"));
  } catch (err) {
    els.runStatus.textContent = t("pipeline.failed");
    showToast(safeErrorMessage(err.payload), true);
  }
}

async function runFile(event) {
  event.preventDefault();

  if (!state.token && cfg.auth_enabled !== false) {
    showToast(t("toast.needLogin"), true);
    return;
  }

  const file = els.fileInput.files?.[0];
  if (!file) {
    showToast(t("toast.selectFile"), true);
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("output_dir", els.fileOutputDir.value.trim());
  formData.append("contract_name", els.fileContract.value.trim());
  formData.append("profile_name", els.fileProfile.value.trim());
  formData.append("template_name", els.fileTemplateName.value.trim());
  formData.append("template_path", els.fileTemplatePath.value.trim());

  els.runStatus.textContent = t("pipeline.runningFile");
  try {
    const { data, res } = await fetchJSON("/process/file", {
      method: "POST",
      headers: {
        ...authHeaders(),
      },
      body: formData,
    });

    const requestId = res.headers.get("x-request-id") || "-";
    const metrics = data?.outcome?.metrics || {};
    metrics.request_id = requestId;

    renderResultJson(data);
    renderMetrics(metrics);
    renderArtifacts(data?.outcome?.artifacts || {});
    await refreshAudit();
    await refreshOpsSummary();
    els.runStatus.textContent = tf("pipeline.success", { requestId });
    showToast(t("toast.fileDone"));
  } catch (err) {
    els.runStatus.textContent = t("pipeline.failed");
    showToast(safeErrorMessage(err.payload), true);
  }
}

async function refreshAudit() {
  if (!state.token && cfg.auth_enabled !== false) {
    renderAudit([]);
    return;
  }

  const query = buildOpsQuery(40);

  try {
    const { data } = await fetchJSON(`/ops/audit/recent?${query}`, {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
    });
    renderAudit(data.events || []);
  } catch (err) {
    if (err.status === 403) {
      renderAudit([]);
      return;
    }
    showToast(t("toast.auditFail"), true);
  }
}

async function refreshOpsSummary() {
  if (!state.token && cfg.auth_enabled !== false) {
    renderOpsSummary(null, null);
    return;
  }

  const query = buildOpsQuery(220);

  try {
    const { data } = await fetchJSON(`/ops/audit/summary?${query}`, {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
    });
    renderOpsSummary(data.summary || null, data.anomalies || null);
  } catch (err) {
    if (err.status === 403) {
      renderOpsSummary(null, null);
      return;
    }
    showToast(t("toast.summaryFail"), true);
  }
}

async function refreshReadiness() {
  if (!state.token && cfg.auth_enabled !== false) {
    renderReadiness(null);
    return;
  }

  try {
    const { data } = await fetchJSON("/ops/readiness", {
      method: "GET",
      headers: {
        ...authHeaders(),
      },
    });
    renderReadiness(data || null);
  } catch (err) {
    if (err.status === 403) {
      renderReadiness(null);
      return;
    }
    showToast(t("toast.readinessFail"), true);
  }
}

function bindEvents() {
  let actorFilterTimer = null;

  els.modePathBtn.addEventListener("click", () => toggleMode("path"));
  els.modeFileBtn.addEventListener("click", () => toggleMode("file"));
  els.loginForm.addEventListener("submit", login);
  els.logoutBtn.addEventListener("click", logout);
  els.pathForm.addEventListener("submit", runPath);
  els.fileForm.addEventListener("submit", runFile);
  els.verifyForm.addEventListener("submit", verifyExportSignature);

  els.refreshAuditBtn.addEventListener("click", async () => {
    await refreshAudit();
    await refreshOpsSummary();
  });
  els.refreshReadinessBtn.addEventListener("click", refreshReadiness);
  if (els.bootstrapRefreshBtn) {
    els.bootstrapRefreshBtn.addEventListener("click", async () => {
      await refreshHealth();
      showToast(t("toast.bootstrapRefreshed"));
    });
  }

  els.langSelect.addEventListener("change", () => {
    state.lang = els.langSelect.value;
    applyI18n();
  });

  els.themeSelect.addEventListener("change", () => {
    state.theme = els.themeSelect.value;
    applyTheme();
    renderOpsSummary(state.lastSummary, state.lastAnomalies);
  });

  els.brandSelect.addEventListener("change", () => {
    state.brand = els.brandSelect.value;
    applyTheme();
    renderOpsSummary(state.lastSummary, state.lastAnomalies);
  });

  els.opsSinceSelect.addEventListener("change", async () => {
    state.opsSinceHours = els.opsSinceSelect.value;
    localStorage.setItem("secure_ops_since", state.opsSinceHours);
    await refreshAudit();
    await refreshOpsSummary();
  });

  els.opsStatusSelect.addEventListener("change", async () => {
    state.opsStatus = els.opsStatusSelect.value;
    localStorage.setItem("secure_ops_status", state.opsStatus);
    await refreshAudit();
    await refreshOpsSummary();
  });

  els.opsEventTypeSelect.addEventListener("change", async () => {
    state.opsEventType = els.opsEventTypeSelect.value;
    localStorage.setItem("secure_ops_event_type", state.opsEventType);
    await refreshAudit();
    await refreshOpsSummary();
  });

  els.opsActorInput.addEventListener("input", () => {
    if (actorFilterTimer) {
      window.clearTimeout(actorFilterTimer);
    }

    actorFilterTimer = window.setTimeout(async () => {
      state.opsActorContains = els.opsActorInput.value;
      localStorage.setItem("secure_ops_actor_contains", state.opsActorContains);
      await refreshAudit();
      await refreshOpsSummary();
    }, 350);
  });

  els.exportSummaryBtn.addEventListener("click", exportOpsSummaryJson);
  els.exportAuditCsvBtn.addEventListener("click", exportAuditCsv);
  if (els.copyServiceBriefBtn) {
    els.copyServiceBriefBtn.addEventListener("click", copyServiceBriefSnapshot);
  }
  if (els.copyReviewPackBtn) {
    els.copyReviewPackBtn.addEventListener("click", copyReviewPackSnapshot);
  }

  els.opsAutoRefresh.addEventListener("change", () => {
    state.opsAutoRefresh = els.opsAutoRefresh.checked;
    localStorage.setItem("secure_ops_auto", String(state.opsAutoRefresh));
  });

  window.addEventListener("resize", () => {
    renderOpsSummary(state.lastSummary, state.lastAnomalies);
  });
}

async function bootstrap() {
  setRevealAnimation();
  initDefaults();
  applyTheme();
  bindEvents();
  toggleMode("path");
  applyI18n();
  await refreshHealth();
  await refreshServiceBrief();
  await refreshReviewPack();
  await refreshMe();
  await refreshAudit();
  await refreshOpsSummary();
  await refreshReadiness();

  window.setInterval(async () => {
    await refreshHealth();
    await refreshServiceBrief();
    await refreshReviewPack();
    if (state.opsAutoRefresh) {
      await refreshAudit();
      await refreshOpsSummary();
      await refreshReadiness();
    }
  }, 25000);
}

bootstrap();
