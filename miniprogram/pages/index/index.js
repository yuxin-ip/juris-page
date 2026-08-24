const { years, loadAllQuestions } = require('../../data/loaders.js');

const TRACKS = ['', '非法学', '法学'];
const TYPES = ['', 'single', 'multiple'];

function termMatches(question, haystack, term) {
  const yearQuestion = term.match(/^(20\d{2})(\d{1,2})$/);
  if (yearQuestion) return question.year === Number(yearQuestion[1]) && question.number === Number(yearQuestion[2]);
  if (/^20\d{2}$/.test(term)) return question.year === Number(term);
  if (term === '法学' || term === '非法学') return question.track === term;
  if (term === '单选' || term === '单选题') return question.type === 'single';
  if (term === '多选' || term === '多选题') return question.type === 'multiple';
  return haystack.includes(term);
}

Page({
  data: {
    query: '',
    trackIndex: 0,
    yearIndex: 0,
    typeIndex: 0,
    trackOptions: ['全部', '非法学', '法学'],
    yearOptions: ['全部年份'].concat(years.map(String)),
    typeOptions: ['全部', '单选', '多选'],
    items: [],
    visibleItems: [],
    resultText: '',
    limit: 80,
    hasActiveFilter: false,
  },

  onLoad() {
    this.allQuestions = loadAllQuestions();
    this.applyFilters();
  },

  onSearch(event) {
    this.setData({ query: event.detail.value }, () => this.applyFilters());
  },

  onTrackChange(event) {
    this.setData({ trackIndex: Number(event.detail.value) }, () => this.applyFilters());
  },

  onYearChange(event) {
    this.setData({ yearIndex: Number(event.detail.value) }, () => this.applyFilters());
  },

  onTypeChange(event) {
    this.setData({ typeIndex: Number(event.detail.value) }, () => this.applyFilters());
  },

  resetFilters() {
    this.setData({ trackIndex: 0, yearIndex: 0, typeIndex: 0 }, () => this.applyFilters());
  },

  showMore() {
    this.setData({ limit: this.data.limit + 80 }, () => this.applyFilters(false));
  },

  goAbout() {
    wx.navigateTo({ url: '/pages/about/about' });
  },

  applyFilters(resetLimit = true) {
    const { query, trackIndex, yearIndex, typeIndex } = this.data;
    const track = TRACKS[trackIndex];
    const year = yearIndex ? Number(years[yearIndex - 1]) : 0;
    const type = TYPES[typeIndex];
    const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    const items = this.allQuestions.filter((question) => {
      if (track && question.track !== track) return false;
      if (year && question.year !== year) return false;
      if (type && question.type !== type) return false;
      const haystack = [question.id, question.year, question.track, question.number, question.primary_topic]
        .concat(question.topics.map((topic) => topic.label)).join(' ').toLowerCase();
      return terms.every((term) => termMatches(question, haystack, term));
    });
    const limit = resetLimit ? 80 : this.data.limit;
    const lawCount = items.filter((item) => item.track === '法学').length;
    const nonlawCount = items.length - lawCount;
    this.setData({
      items,
      visibleItems: items.slice(0, limit),
      limit,
      hasActiveFilter: Boolean(track || year || type),
      resultText: `找到 ${items.length} 道题（法学 ${lawCount} · 非法学 ${nonlawCount}）`,
    });
  }
});
