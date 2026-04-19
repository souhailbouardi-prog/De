export const TOOL_VERBS: Record<string, string> = {
  browser: 'browsing',
  clarify: 'asking',
  create_file: 'creating',
  delegate_task: 'delegating',
  delete_file: 'deleting',
  execute_code: 'executing',
  image_generate: 'generating',
  list_files: 'listing',
  memory: 'remembering',
  patch: 'patching',
  read_file: 'reading',
  run_command: 'running',
  search_code: 'searching',
  search_files: 'searching',
  terminal: 'terminal',
  web_extract: 'extracting',
  web_search: 'searching',
  write_file: 'writing'
}

export const VERBS = [
  'pondering',
  'contemplating',
  'musing',
  'cogitating',
  'ruminating',
  'deliberating',
  'mulling',
  'reflecting',
  'processing',
  'reasoning',
  'analyzing',
  'computing',
  'synthesizing',
  'formulating',
  'brainstorming'
]

export const VERBS_ZH = [
  '思考中',
  '琢磨中',
  '沉吟中',
  '深思中',
  '回味中',
  '斟酌中',
  '考虑中',
  '反思中',
  '处理中',
  '推理中',
  '分析中',
  '计算中',
  '综合中',
  '构思中',
  '头脑风暴'
]

/** Returns the verb array for the current browser locale. */
export function getVerbs(): string[] {
  const lang = typeof navigator !== 'undefined' ? navigator.language : ''
  return lang.startsWith('zh') ? VERBS_ZH : VERBS
}
