<script setup lang="ts">
import { computed } from "vue"

import type { ResumePayload } from "../lib/drafts"

const props = defineProps<{
  resume: ResumePayload
}>()

const visibility = computed(() => props.resume.sectionVisibility)

const contactLine = computed(() => {
  const basic = props.resume.basic
  return [basic.phone, basic.email, basic.city].filter((item) => item.trim()).join(" · ")
})

const intentLine = computed(() => {
  const job = props.resume.job
  return [job.targetRole, job.expectedSalary, job.employmentType]
    .filter((item) => item.trim())
    .join(" · ")
})

const educationRows = computed(() =>
  visibility.value.education
    ? props.resume.education.filter((item) => `${item.school}${item.major}${item.degree}`.trim())
    : [],
)
const employmentRows = computed(() =>
  visibility.value.employment
    ? props.resume.employment.filter((item) => `${item.company}${item.position}`.trim())
    : [],
)
const projectRows = computed(() =>
  visibility.value.projects
    ? props.resume.projects.filter((item) => `${item.name}${item.description}`.trim())
    : [],
)

function dateRange(start: string, end: string): string {
  return [start, end].filter((item) => item.trim()).join(" – ")
}
</script>

<template>
  <div class="resume-print-sheet" role="document" aria-label="简历打印视图">
    <header class="print-header">
      <h1>{{ resume.basic.name || "未命名" }}</h1>
      <p v-if="intentLine" class="print-intent">求职意向：{{ intentLine }}</p>
      <p v-if="contactLine" class="print-contact">{{ contactLine }}</p>
    </header>

    <section v-if="educationRows.length" class="print-section">
      <h2>教育经历</h2>
      <article v-for="(item, index) in educationRows" :key="`edu-${index}`" class="print-entry">
        <div class="print-entry-head">
          <strong>{{ item.school }}</strong><span>{{ dateRange(item.startDate, item.endDate) }}</span>
        </div>
        <p class="print-entry-sub">{{ [item.major, item.degree].filter((part) => part.trim()).join(" · ") }}</p>
      </article>
    </section>

    <section v-if="employmentRows.length" class="print-section">
      <h2>工作经历</h2>
      <article v-for="(item, index) in employmentRows" :key="`emp-${index}`" class="print-entry">
        <div class="print-entry-head">
          <strong>{{ item.company }}</strong><span>{{ dateRange(item.startDate, item.endDate) }}</span>
        </div>
        <p class="print-entry-sub">{{ item.position }}</p>
        <p v-if="item.description" class="print-entry-body">{{ item.description }}</p>
      </article>
    </section>

    <section v-if="projectRows.length" class="print-section">
      <h2>项目经历</h2>
      <article v-for="(item, index) in projectRows" :key="`prj-${index}`" class="print-entry">
        <div class="print-entry-head">
          <strong>{{ item.name }}</strong><span>{{ dateRange(item.startDate, item.endDate) }}</span>
        </div>
        <p v-if="item.role" class="print-entry-sub">{{ item.role }}</p>
        <p v-if="item.description" class="print-entry-body">{{ item.description }}</p>
      </article>
    </section>

    <section v-if="visibility.skills && (resume.skills.skills.length || resume.skills.certificates.length)" class="print-section">
      <h2>技能与证书</h2>
      <p v-if="resume.skills.skills.length" class="print-line"><strong>技能：</strong>{{ resume.skills.skills.join(" · ") }}</p>
      <p v-if="resume.skills.certificates.length" class="print-line"><strong>证书：</strong>{{ resume.skills.certificates.join(" · ") }}</p>
    </section>

    <section v-if="visibility.selfEvaluation && resume.selfEvaluation.trim()" class="print-section">
      <h2>自我评价</h2>
      <p class="print-line">{{ resume.selfEvaluation }}</p>
    </section>

    <footer v-if="!educationRows.length && !employmentRows.length && !projectRows.length && !(visibility.skills && (resume.skills.skills.length || resume.skills.certificates.length)) && !(visibility.selfEvaluation && resume.selfEvaluation.trim())" class="print-empty">
      简历内容为空——回到编辑器填写后即可打印或导出。
    </footer>
  </div>
</template>

<style scoped>
.resume-print-sheet { display: none; }
.resume-print-sheet.is-open { display: block; }

@media print {
  @page { size: A4; margin: 14mm; }
  body * { visibility: hidden !important; }
  .resume-print-sheet,
  .resume-print-sheet * { visibility: visible !important; }
  .resume-print-sheet.is-open { position: absolute; left: 0; top: 0; width: 100%; background: #fff; color: #111; }
}

.resume-print-sheet { color: #111; background: #fff; font-family: "Source Han Serif SC", "Noto Serif SC", "SimSun", serif; }
.print-header { text-align: center; border-bottom: 2px solid #111; padding-bottom: 10px; }
.print-header h1 { margin: 0; font-size: 26px; letter-spacing: 2px; }
.print-intent { margin: 6px 0 0; font-size: 14px; font-weight: 600; }
.print-contact { margin: 4px 0 0; font-size: 12px; color: #444; }
.print-section { margin-top: 18px; }
.print-section h2 { margin: 0 0 8px; font-size: 15px; border-left: 4px solid #111; padding-left: 8px; }
.print-entry { margin-bottom: 10px; }
.print-entry-head { display: flex; justify-content: space-between; gap: 12px; font-size: 13px; }
.print-entry-head span { color: #555; white-space: nowrap; }
.print-entry-sub { margin: 2px 0 0; font-size: 12px; color: #333; }
.print-entry-body { margin: 4px 0 0; font-size: 12px; line-height: 1.6; }
.print-line { margin: 0; font-size: 12px; line-height: 1.6; }
.print-empty { margin-top: 24px; font-size: 13px; color: #777; text-align: center; }
</style>
