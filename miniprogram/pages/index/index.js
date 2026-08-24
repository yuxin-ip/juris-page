const { years, loadAllQuestions } = require('../../data/loaders.js');
const { groups } = require('../../data/topic-filters.js');

const TRACKS = ['', '非法学', '法学'];
const TYPES = ['', 'single', 'multiple'];
const SUBJECTS = ['', '刑法', '民法'];

function availableGroups(subject) { return subject ? groups.filter((item) => item.subject === subject) : groups; }
function categoryOptions(subject) { return ['全部门类'].concat(availableGroups(subject).map((item) => item.label)); }
function allTopics(category, subject) {
  const selected = groups.find((item) => item.label === category);
  return ['全部知识点'].concat(selected ? selected.topics : availableGroups(subject).flatMap((item) => item.topics));
}

function termMatches(question, haystack, term) {
  const yearQuestion = term.match(/^(20\d{2})(\d{1,2})$/);
  if (yearQuestion) return question.year === Number(yearQuestion[1]) && question.number === Number(yearQuestion[2]);
  if (/^20\d{2}$/.test(term)) return question.year === Number(term);
  if (term === '法学' || term === '非法学') return question.track === term;
  if (term === '刑法' || term === '民法') return question.subject === term;
  if (term === '单选' || term === '单选题') return question.type === 'single';
  if (term === '多选' || term === '多选题') return question.type === 'multiple';
  return haystack.includes(term);
}

Page({
  data: {
    query: '', trackIndex: 0, yearIndex: 0, typeIndex: 0, subjectIndex: 0, categoryIndex: 0, topicIndex: 0,
    trackOptions: ['全部', '非法学', '法学'],
    yearOptions: ['全部年份'].concat(years.map(String)),
    typeOptions: ['全部', '单选', '多选'],
    subjectOptions: ['全部科目', '刑法', '民法'],
    categoryOptions: categoryOptions(''),
    topicOptions: allTopics('', ''), topicFilterTitle: '知识点筛选', categoryCaption: '知识门类', topicCaption: '具体知识点',
    items: [], visibleItems: [], resultText: '', endText: '', limit: 80,
    hasActiveFilter: false, hasMore: false, showEndHint: false,
  },

  onLoad() { this.allQuestions = loadAllQuestions(); this.applyFilters(); },
  onSearch(event) { this.setData({ query: event.detail.value }, () => this.applyFilters()); },
  onTrackChange(event) { this.setData({ trackIndex: Number(event.detail.value) }, () => this.applyFilters()); },
  onYearChange(event) { this.setData({ yearIndex: Number(event.detail.value) }, () => this.applyFilters()); },
  onTypeChange(event) { this.setData({ typeIndex: Number(event.detail.value) }, () => this.applyFilters()); },

  onSubjectChange(event) {
    const subjectIndex = Number(event.detail.value);
    const subject = SUBJECTS[subjectIndex];
    this.setData({
      subjectIndex, categoryIndex: 0, topicIndex: 0,
      categoryOptions: categoryOptions(subject), topicOptions: allTopics('', subject),
      topicFilterTitle: subject === '刑法' ? '刑法分则罪名' : subject === '民法' ? '民法编号知识点' : '知识点筛选',
      categoryCaption: subject === '刑法' ? '犯罪类型' : subject === '民法' ? '民法部分' : '知识门类',
      topicCaption: subject === '刑法' ? '具体罪名' : '具体知识点',
    }, () => this.applyFilters());
  },

  onCategoryChange(event) {
    const categoryIndex = Number(event.detail.value);
    const category = this.data.categoryOptions[categoryIndex];
    const subject = SUBJECTS[this.data.subjectIndex];
    this.setData({
      categoryIndex, topicIndex: 0,
      topicOptions: allTopics(categoryIndex ? category : '', subject),
    }, () => this.applyFilters());
  },

  onTopicChange(event) { this.setData({ topicIndex: Number(event.detail.value) }, () => this.applyFilters()); },

  resetFilters() {
    this.setData({
      trackIndex: 0, yearIndex: 0, typeIndex: 0, subjectIndex: 0, categoryIndex: 0, topicIndex: 0,
      categoryOptions: categoryOptions(''), topicOptions: allTopics('', ''),
      topicFilterTitle: '知识点筛选', categoryCaption: '知识门类', topicCaption: '具体知识点',
    }, () => this.applyFilters());
  },

  showMore() { this.setData({ limit: this.data.limit + 80 }, () => this.applyFilters(false)); },
  goAbout() { wx.navigateTo({ url: '/pages/about/about' }); },

  applyFilters(resetLimit = true) {
    const { query, trackIndex, yearIndex, typeIndex, subjectIndex, categoryIndex, topicIndex, categoryOptions, topicOptions } = this.data;
    const track = TRACKS[trackIndex];
    const year = yearIndex ? Number(years[yearIndex - 1]) : 0;
    const type = TYPES[typeIndex];
    const subject = SUBJECTS[subjectIndex];
    const category = categoryIndex ? categoryOptions[categoryIndex] : '';
    const topic = topicIndex ? topicOptions[topicIndex] : '';
    const categoryTopics = new Set((groups.find((item) => item.label === category) || { topics: [] }).topics);
    const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const items = this.allQuestions.filter((question) => {
      if (track && question.track !== track) return false;
      if (year && question.year !== year) return false;
      if (type && question.type !== type) return false;
      if (subject && question.subject !== subject) return false;
      if (category && !question.topics.some((item) => categoryTopics.has(item.label))) return false;
      if (topic && !question.topics.some((item) => item.label === topic)) return false;
      const haystack = [question.id, question.year, question.track, question.subject, question.number, question.primary_topic]
        .concat(question.topics.map((topic) => topic.label)).join(' ').toLowerCase();
      return terms.every((term) => termMatches(question, haystack, term));
    });
    const limit = resetLimit ? 80 : this.data.limit;
    const lawCount = items.filter((item) => item.track === '法学').length;
    const nonlawCount = items.length - lawCount;
    const hasMore = items.length > limit;
    this.setData({
      items, visibleItems: items.slice(0, limit), limit, hasMore,
      showEndHint: items.length > 0 && !hasMore,
      endText: `没有更多内容了，已显示全部 ${items.length} 道题。`,
      hasActiveFilter: Boolean(track || year || type || subject || category || topic),
      resultText: `找到 ${items.length} 道题（法学 ${lawCount} · 非法学 ${nonlawCount}）`,
    });
  }
});
