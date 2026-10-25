// Orbit carousel: arrows, mission-path stops, and arrow-key travel for a
// scroll-snap track. Without this script the track is still a swipeable row.
(function () {
    var smooth = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    document.querySelectorAll('[data-orbit-carousel]').forEach(function (root) {
        var track = root.querySelector('.orbit-track');
        var slides = Array.prototype.slice.call(track.children);
        var stops = Array.prototype.slice.call(root.querySelectorAll('.orbit-stop'));
        var prev = root.querySelector('.orbit-prev');
        var next = root.querySelector('.orbit-next');
        var controls = root.querySelector('.orbit-controls');
        var current = -1;

        function offsetOf(slide) {
            return slide.offsetLeft - parseFloat(getComputedStyle(track).paddingLeft);
        }

        function setCurrent(index) {
            if (index === current) return;
            current = index;
            stops.forEach(function (stop, i) {
                stop.setAttribute('aria-current', i === index ? 'true' : 'false');
            });
            prev.disabled = index === 0;
            next.disabled = index === slides.length - 1;
        }

        function go(index) {
            index = Math.max(0, Math.min(slides.length - 1, index));
            track.scrollTo({ left: offsetOf(slides[index]), behavior: smooth ? 'smooth' : 'auto' });
            setCurrent(index);
        }

        // The current slide is the one whose start is nearest the scroll position.
        function sync() {
            var nearest = 0;
            var best = Infinity;
            slides.forEach(function (slide, i) {
                var distance = Math.abs(offsetOf(slide) - track.scrollLeft);
                if (distance < best) {
                    best = distance;
                    nearest = i;
                }
            });
            // At the far end the last slide may never reach the start edge.
            if (track.scrollLeft + track.clientWidth >= track.scrollWidth - 2) {
                nearest = slides.length - 1;
            }
            setCurrent(nearest);
        }

        var pending = false;
        track.addEventListener('scroll', function () {
            if (pending) return;
            pending = true;
            requestAnimationFrame(function () {
                pending = false;
                sync();
            });
        }, { passive: true });

        prev.addEventListener('click', function () { go(current - 1); });
        next.addEventListener('click', function () { go(current + 1); });
        stops.forEach(function (stop, i) {
            stop.addEventListener('click', function () { go(i); });
        });
        track.addEventListener('keydown', function (event) {
            if (event.target !== track) return;
            if (event.key === 'ArrowRight') {
                event.preventDefault();
                go(current + 1);
            } else if (event.key === 'ArrowLeft') {
                event.preventDefault();
                go(current - 1);
            }
        });

        controls.hidden = false;
        sync();
    });
}());
