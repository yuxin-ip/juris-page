const { years, loadAllQuestions } = require('../../data/loaders.js');
const { groups } = require('../../data/topic-filters.js');

const TRACKS = ['', '非法学', '法学'];
const TYPES = ['', 'single', 'multiple'];
const SUBJECTS = ['刑法', '民法'];

function selectedSubjects(selected) {
  return SUBJECTS.filter((_subject, index) => selected[index]);
}

function singleSubject(selected) {
  const subjects = selectedSubjects(selected);
  return subjects.length === 1 ? subjects[0] : '';
}

function availableGroups(subject) { return subject ? groups.filter((item) => item.subject === subject) : groups; }
function categoryOptions(subject) {
  const first = subject === '刑法' ? '犯罪类型' : subject === '民法' ? '民法典全部七编' : '';
  return [first].concat(availableGroups(subject).map((item) => item.label));
}
function allTopics(category, subject) {
  const selected = groups.find((item) => item.label === category);
  const first = subject === '刑法' ? '具体罪名' : '具体知识点';
  return [first].concat(selected ? selected.topics : availableGroups(subject).flatMap((item) => item.topics));
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
    query: '', trackIndex: 0, yearIndex: 0, typeIndex: 0, subjectSelected: [false, false], categoryIndex: 0, topicIndex: 0,
    trackOptions: ['全部', '非法学', '法学'],
    yearOptions: ['全部年份'].concat(years.map(String)),
    typeOptions: ['全部', '单选', '多选'],
    subjectOptions: ['刑法', '民法'],
    categoryOptions: [], topicOptions: [], topicFilterTitle: '',
    items: [], visibleItems: [], resultText: '', endText: '', limit: 80,
    hasActiveFilter: false, subjectPanelActive: false, showTopicFilters: false, hasMore: false, showEndHint: false,
    showBackToFilters: false, backToFiltersArmed: false,
  },

  onLoad() { this.allQuestions = loadAllQuestions(); this.applyFilters(); },
  onSearch(event) { this.setData({ query: event.detail.value }, () => this.applyFilters()); },
  onTrackChange(event) { this.setData({ trackIndex: Number(event.detail.value) }, () => this.applyFilters(true, true)); },
  onYearChange(event) { this.setData({ yearIndex: Number(event.detail.value) }, () => this.applyFilters(true, true)); },
  onTypeChange(event) { this.setData({ typeIndex: Number(event.detail.value) }, () => this.applyFilters(true, true)); },

  onSubjectTap(event) {
    const index = Number(event.currentTarget.dataset.index);
    const subjectSelected = this.data.subjectSelected.slice();
    subjectSelected[index] = !subjectSelected[index];
    const subject = singleSubject(subjectSelected);
    this.setData({
      subjectSelected, categoryIndex: 0, topicIndex: 0,
      categoryOptions: subject ? categoryOptions(subject) : [], topicOptions: subject ? allTopics('', subject) : [],
      topicFilterTitle: subject === '刑法' ? '刑法分则罪名' : subject === '民法' ? '民法编号知识点' : '',
      subjectPanelActive: Boolean(subject), showTopicFilters: Boolean(subject),
    }, () => this.applyFilters(true, true));
  },

  onCategoryChange(event) {
    const categoryIndex = Number(event.detail.value);
    const category = this.data.categoryOptions[categoryIndex];
    const subject = singleSubject(this.data.subjectSelected);
    this.setData({
      categoryIndex, topicIndex: 0,
      topicOptions: allTopics(categoryIndex ? category : '', subject),
    }, () => this.applyFilters(true, true));
  },

  onTopicChange(event) { this.setData({ topicIndex: Number(event.detail.value) }, () => this.applyFilters(true, true)); },

  resetFilters() {
    this.setData({
      trackIndex: 0, yearIndex: 0, typeIndex: 0, subjectSelected: [false, false], categoryIndex: 0, topicIndex: 0,
      categoryOptions: [], topicOptions: [], topicFilterTitle: '',
      subjectPanelActive: false, showTopicFilters: false,
    }, () => this.applyFilters(true, true));
  },

  showMore() { this.setData({ limit: this.data.limit + 80 }, () => this.applyFilters(false)); },
  goAbout() { wx.navigateTo({ url: '/pages/about/about' }); },

  scrollToResults() {
    const query = wx.createSelectorQuery().in(this);
    query.select('#resultStart').boundingClientRect();
    query.selectViewport().scrollOffset();
    query.exec((result) => {
      if (!result[0] || !result[1]) return;
      wx.pageScrollTo({ scrollTop: Math.max(0, result[0].top + result[1].scrollTop - 16), duration: 260 });
    });
  },

  onPageScroll(event) {
    const showBackToFilters = event.scrollTop > 560;
    if (showBackToFilters !== this.data.showBackToFilters) this.setData({ showBackToFilters });
  },

  onBackToFilters() {
    if (!this.data.backToFiltersArmed) {
      this.setData({ backToFiltersArmed: true });
      clearTimeout(this.backToFiltersTimer);
      this.backToFiltersTimer = setTimeout(() => this.setData({ backToFiltersArmed: false }), 2200);
      return;
    }
    clearTimeout(this.backToFiltersTimer);
    this.setData({ backToFiltersArmed: false });
    wx.pageScrollTo({ scrollTop: 0, duration: 260 });
  },

  onUnload() { clearTimeout(this.backToFiltersTimer); },

  applyFilters(resetLimit = true, jumpToResults = false) {
    const { query, trackIndex, yearIndex, typeIndex, subjectSelected, categoryIndex, topicIndex, categoryOptions, topicOptions } = this.data;
    const track = TRACKS[trackIndex];
    const year = yearIndex ? Number(years[yearIndex - 1]) : 0;
    const type = TYPES[typeIndex];
    const subject = singleSubject(subjectSelected);
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
    }, () => { if (jumpToResults) this.scrollToResults(); });
  }
});
