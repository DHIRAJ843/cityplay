document.addEventListener("DOMContentLoaded", function () {
  var latInput = document.getElementById("id_latitude");
  var lngInput = document.getElementById("id_longitude");
  if (!latInput || !lngInput) return;

  var defaultLat = 23.2156;
  var defaultLng = 72.6369;
  var startLat = parseFloat(latInput.value) || defaultLat;
  var startLng = parseFloat(lngInput.value) || defaultLng;

  // ---------- Build the map ----------
  var latRow = latInput.closest(".form-row") || latInput.closest("div");
  var mapDiv = document.createElement("div");
  mapDiv.id = "location-picker-map";
  mapDiv.style.height = "350px";
  mapDiv.style.marginBottom = "15px";
  mapDiv.style.borderRadius = "8px";
  latRow.parentNode.insertBefore(mapDiv, latRow);

  var hint = document.createElement("p");
  hint.textContent = "Click the map to fine-tune, or use the box above to auto-locate by address / Google Maps link.";
  hint.style.fontSize = "12px";
  hint.style.opacity = "0.7";
  hint.style.marginBottom = "8px";
  mapDiv.parentNode.insertBefore(hint, mapDiv);

  var map = L.map("location-picker-map").setView([startLat, startLng], 14);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19
  }).addTo(map);
  var marker = L.marker([startLat, startLng], { draggable: true }).addTo(map);

  function setLocation(lat, lng, zoom) {
    lat = parseFloat(lat);
    lng = parseFloat(lng);
    latInput.value = lat.toFixed(6);
    lngInput.value = lng.toFixed(6);
    marker.setLatLng([lat, lng]);
    map.setView([lat, lng], zoom || 16);
  }

  map.on("click", function (e) {
    setLocation(e.latlng.lat, e.latlng.lng);
  });

  marker.on("dragend", function () {
    var pos = marker.getLatLng();
    setLocation(pos.lat, pos.lng);
  });

  // ---------- "Find location" box ----------
  var finderWrap = document.createElement("div");
  finderWrap.style.marginBottom = "10px";
  finderWrap.style.display = "flex";
  finderWrap.style.gap = "8px";

  var finderInput = document.createElement("input");
  finderInput.type = "text";
  finderInput.placeholder = "Paste a Google Maps link, or type an address, then click Locate";
  finderInput.style.flex = "1";
  finderInput.style.padding = "6px 8px";

  var finderBtn = document.createElement("button");
  finderBtn.type = "button";
  finderBtn.textContent = "Locate";
  finderBtn.className = "button";

  var finderStatus = document.createElement("span");
  finderStatus.style.fontSize = "12px";
  finderStatus.style.marginLeft = "8px";
  finderStatus.style.opacity = "0.8";
  finderStatus.style.display = "block";
  finderStatus.style.marginBottom = "8px";

  finderWrap.appendChild(finderInput);
  finderWrap.appendChild(finderBtn);
  hint.parentNode.insertBefore(finderWrap, hint);
  hint.parentNode.insertBefore(finderStatus, hint);

  function extractLatLngFromUrl(text) {
    var patterns = [
      /@(-?\d+\.\d+),(-?\d+\.\d+)/,
      /!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)/,
      /[?&]q=(-?\d+\.\d+),(-?\d+\.\d+)/
    ];
    for (var i = 0; i < patterns.length; i++) {
      var m = text.match(patterns[i]);
      if (m) {
        return { lat: m[1], lng: m[2] };
      }
    }
    return null;
  }

  function geocodeAddress(query) {
    finderStatus.textContent = "Searching...";
    fetch("https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + encodeURIComponent(query))
      .then(function (r) { return r.json(); })
      .then(function (results) {
        if (results && results.length > 0) {
          setLocation(results[0].lat, results[0].lon, 16);
          finderStatus.textContent = "Found: " + results[0].display_name.split(",").slice(0, 3).join(",");
        } else {
          finderStatus.textContent = "No match found. Try a shorter address or paste a Google Maps link instead.";
        }
      })
      .catch(function () {
        finderStatus.textContent = "Lookup failed. Check your internet connection.";
      });
  }

  finderBtn.addEventListener("click", function () {
    var text = finderInput.value.trim();
    if (!text) {
      return;
    }

    var coords = extractLatLngFromUrl(text);
    if (coords) {
      setLocation(coords.lat, coords.lng, 17);
      finderStatus.textContent = "Location set from map link.";
      return;
    }

    if (/^https?:\/\//i.test(text)) {
      finderStatus.textContent = "Resolving link...";
      fetch("/venues/resolve-map-link/?url=" + encodeURIComponent(text))
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data.lat && data.lng) {
            setLocation(data.lat, data.lng, 17);
            finderStatus.textContent = "Location set from map link.";
          } else {
            finderStatus.textContent = data.error || "Could not read that link.";
          }
        })
        .catch(function () {
          finderStatus.textContent = "Could not resolve that link.";
        });
      return;
    }

    geocodeAddress(text);
  });

  finderInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      finderBtn.click();
    }
  });
});