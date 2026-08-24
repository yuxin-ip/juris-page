Component({
  properties: {
    question: { type: Object, value: {} }
  },
  data: { expanded: false },
  methods: {
    toggleMore() {
      this.setData({ expanded: !this.data.expanded });
    }
  }
});
