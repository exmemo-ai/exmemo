<template>
  <div id="app">
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  name: 'App',
};

// Debug: ResizeObserver loop completed with undelivered notifications.
const debounce = (fn, delay) => {
  let timer = null;
  return function () {
    let context = this;
    let args = arguments;
    clearTimeout(timer);
    timer = setTimeout(function () {
      fn.apply(context, args);
    }, delay);
  };
};

const _ResizeObserver = window.ResizeObserver;
window.ResizeObserver = class ResizeObserver extends _ResizeObserver {
  constructor(callback) {
    const safeCallback = (entries, observer) => {
      try {
        const validEntries = entries.filter(entry => {
          const target = entry.target;
          return target && typeof target.getBoundingClientRect === 'function';
        });
        
        if (validEntries.length > 0) {
          callback(validEntries, observer);
        }
      } catch (error) {
        console.warn('ResizeObserver callback error:', error);
      }
    };
    
    super(debounce(safeCallback, 16));
  }
};
</script>

<style>

</style>
