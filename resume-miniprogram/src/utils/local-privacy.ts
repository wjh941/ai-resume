import { PENDING_KEY } from "../stores/applications"
import { CHECKPOINT_KEY as CAREER_CHECKPOINT_KEY } from "../stores/career"
import { CONSULTATION_STATE_KEY } from "../stores/consultation"
import { CHECKPOINT_KEY as RESUME_CHECKPOINT_KEY } from "../stores/resume"
import { userStorageKey } from "../stores/session"
import { getUniStorage } from "./persistence"

// resume_demo_assessment 是历史版本遗留键：测评结果现在仅存内存，
// 保留此键只为清理旧设备上的残留数据。
const LEGACY_ASSESSMENT_KEY = "resume_demo_assessment"

// 键清单从各 store 导入常量，store 侧改名会在编译期暴露，不再漂移。
const LOCAL_CAREER_WORKSPACE_KEYS = [
  RESUME_CHECKPOINT_KEY,
  CAREER_CHECKPOINT_KEY,
  CONSULTATION_STATE_KEY,
  LEGACY_ASSESSMENT_KEY,
  PENDING_KEY,
] as const

export function clearLocalCareerWorkspace(): void {
  const storage = getUniStorage()
  if (!storage) return
  for (const key of LOCAL_CAREER_WORKSPACE_KEYS) {
    storage.removeStorageSync?.(key)
    storage.removeStorageSync?.(userStorageKey(key))
  }
}
