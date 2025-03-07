// Initialize the map
const map = L.map("map").setView([41.3879, 2.16992], 13);

// Add OpenStreetMap tiles
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "© OpenStreetMap contributors",
}).addTo(map);

// Variables to store active markers, radius circle, area, home marker
let activeMarkers = [];
let activeCircle = null;
let activeArea = null;
let homeMarker = null;

const resultList = document.getElementById("result-list"); // Reference to the result list container

// Define a custom home icon
const homeIcon = L.icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/69/69524.png",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
});

// Function to clear all active markers, radius circle, area, home marker, and result list
function clearMap() {
  activeMarkers.forEach((marker) => map.removeLayer(marker));
  activeMarkers = [];
  if (activeCircle) {
    map.removeLayer(activeCircle);
    activeCircle = null;
  }
  if (activeArea) {
    map.removeLayer(activeArea);
    activeArea = null;
  }
  if (homeMarker) {
    map.removeLayer(homeMarker);
    homeMarker = null;
  }
  resultList.innerHTML = "<p>No results found.</p>"; // Clear result list
}

let currentChart = null; // Variable to store the current chart instance
let allPlots = []; // Store plots for all items

// Function to display all plots
function displayAllPlots(remainingPlacesData, features) {
  const ctx = document.getElementById("remainingPlacesChart").getContext("2d");

  // Destroy the current chart if it exists
  if (currentChart) {
    currentChart.destroy();
  }

  const dates = remainingPlacesData[0].map((item) => item[0]); // Assuming same dates for all features
  const datasets = features.map((feature, index) => ({
    label: feature.properties["denominaci_completa"],
    data: remainingPlacesData[index].map((item) => item[1]),
    borderColor: `rgb(${(index * 60) % 255}, ${(index * 100) % 255}, ${(index * 150) % 255})`,
    fill: false,
  }));

  // Create a new chart with all plots
  currentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: dates,
      datasets: datasets,
    },
    options: {
      responsive: true,
      scales: {
        x: {
          type: "category",
          title: {
            display: true,
            text: "Data",
          },
        },
        y: {
          title: {
            display: true,
            text: "Places vacants a I3",
          },
          beginAtZero: true,
        },
      },
    },
  });
}

// Get random color for each dataset
function getRandomColor() {
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}

// Function to handle item click and toggle visibility of the plot for that item
function handleItemClick(index) {
  // Toggle visibility for the selected plot
  const dataset = currentChart.data.datasets[index];
  dataset.hidden = !dataset.hidden; // Toggle visibility

  // If the dataset is hidden, only show the selected plot, otherwise show all plots
  if (dataset.hidden) {
    // Hide all other plots
    currentChart.data.datasets.forEach((data, idx) => {
      if (idx !== index) {
        data.hidden = true;
      }
    });
  } else {
    // Show all plots
    currentChart.data.datasets.forEach((data, idx) => {
      data.hidden = false;
    });
  }

  // Update the chart
  currentChart.update();
}

// Function to fetch and display nearby markers
function fetchAndDisplayNearbyMarkers(lat, lng) {
  const distanceRange = document.getElementById("distance-range");
  const radius = parseFloat(distanceRange.value); // Get the custom distance value
  const toggleSwitch = document.getElementById("toggle-switch");
  const selectedOption = toggleSwitch.checked ? "max_points" : "all_centers";

  fetch(
    `/projects/escoles/nearby?lat=${lat}&lng=${lng}&radius=${radius}&option=${selectedOption}`,
  )
    .then((response) => response.json())
    .then((data) => {
      resultList.innerHTML = ""; // Clear the previous results

      // Check if the area is "Out of bounds"
      if (data.area === "Out of bounds") {
        resultList.innerHTML = "<p>Ubicació fora de Barcelona.</p>";
        return;
      }

      // Draw the radius circle
      if (activeCircle) {
        map.removeLayer(activeCircle);
      }
      activeCircle = L.circle([lat, lng], {
        color: "blue",
        fillColor: "#a3c9ff",
        fillOpacity: 0.3,
        radius: radius,
      }).addTo(map);

      // Draw the detected area if any
      if (data.area && selectedOption === "max_points") {
        if (activeArea) {
          map.removeLayer(activeArea);
        }
        activeArea = L.geoJSON(data.area, {
          style: { color: "purple", fillOpacity: 0.2 },
        }).addTo(map);
      } else if (selectedOption === "all_centers" && activeArea) {
        map.removeLayer(activeArea);
      }

      const sortedFeatures = data.features.sort(
        (a, b) => a.properties.distance_to_home - b.properties.distance_to_home,
      );

      // Function to filter and display results based on checkboxes
      let currentlySelectedItem = null; // Variable to track the currently selected item

      let allPlotsDisplayed = true; // Set this to true to show all plots initially

      function filterResults() {
        const showPublics = document.getElementById("filter-publics").checked;
        const showConcertats =
          document.getElementById("filter-concertats").checked;
        const showPrivats = document.getElementById("filter-privats").checked;

        // Clear the map and the list
        activeMarkers.forEach((marker) => map.removeLayer(marker));
        activeMarkers = [];
        resultList.innerHTML = "";

        // Filter the features and prepare the list
        const filteredFeatures = sortedFeatures.filter((feature) => {
          const naturalesa = feature.properties["nom_naturalesa"];
          const isPublic = naturalesa === "Públic";
          const isConcertat = naturalesa === "Concertat";
          const isPrivat = naturalesa === "Privat";
          return (
            (isPublic && showPublics) ||
            (isConcertat && showConcertats) ||
            (isPrivat && showPrivats)
          );
        });

        // Re-add filtered markers and items to the list
        filteredFeatures.forEach((feature) => {
          const coords = feature.geometry.coordinates;
          const titularitat = feature.properties["nom_titularitat"];
          const naturalesa = feature.properties["nom_naturalesa"];
          const distance = feature.properties["distance_to_home"]; // Get distance from backend

          // Determine marker color
          const markerColor = naturalesa === "Públic" ? "blue" : "green";

          // Create a marker with the color-coded icon
          const marker = L.circleMarker([coords[1], coords[0]], {
            radius: 8,
            fillColor: markerColor,
            color: markerColor,
            weight: 1,
            fillOpacity: 0.8,
          }).bindPopup(`
                    <strong>${feature.properties["denominaci_completa"]}</strong><br>
                    Distància a casa: ${distance.toFixed(2)} metres<br>
                    Adreça: <a href="${feature.properties["adre_a_maps"]}"
                              target="_blank"
                              rel="noopener noreferrer">
                              ${feature.properties["adre_a"]}
                            </a><br>
                    Districte: ${feature.properties["nom_dm"]}<br>
                    Web: <a href="${feature.properties["url"]}"
                           target="_blank"
                           rel="noopener noreferrer">
                           ${feature.properties["url"]}
                        </a><br>
                    Email: ${feature.properties["e_mail_centre"]}<br>
                    Telèfon: ${feature.properties["tel_fon_centre"]}<br>
                    Tipus: ${feature.properties["nom_naturalesa"]}<br>
                    Titularitat: ${titularitat || "Unknown"}<br>
                `);

          marker.addTo(map);
          activeMarkers.push(marker);

          // Add to the results list
          const resultItem = document.createElement("div");
          resultItem.className = "result-item";
          resultItem.innerHTML = `
                    <div class="result-title">${feature.properties["denominaci_completa"]}</div>
                    <div>Distància a casa: ${distance.toFixed(2)} metres</div>
                    <div>Places ofertades el darrer any: ${feature.properties["total_places"]}</div>
                    <div>Places vacants després de les assigacions el darrer any:     ${feature.properties["remaining_places"].length > 0 ? feature.properties["remaining_places"][feature.properties["remaining_places"].length - 1][1] : "N/A"}</div>
                    <div>
                        Adreça:
                        <a href="${feature.properties["adre_a_maps"]}"
                           target="_blank"
                           rel="noopener noreferrer">
                           ${feature.properties["adre_a"]}
                        </a>
                    </div>
                    <div>Districte: ${feature.properties["nom_dm"]}</div>
                    <div>
                        Web:
                        <a href="${feature.properties["url"]}"
                           target="_blank"
                           rel="noopener noreferrer">
                           ${feature.properties["url"]}
                        </a>
                    </div>
                    <div>Email: ${feature.properties["e_mail_centre"]}</div>
                    <div>Telèfon: ${feature.properties["tel_fon_centre"]}</div>
                    <div>Tipus: ${feature.properties["nom_naturalesa"]}</div>
                    <div>Titularitat: ${titularitat || "Unknown"}</div>
                `;

          // Handle item selection or unselection
          resultItem.addEventListener("click", () => {
            if (currentlySelectedItem === resultItem) {
              // If the item is already selected, unselect it
              resultItem.classList.remove("selected");
              currentlySelectedItem = null;

              // Show all plots again
              displayAllPlots(
                filteredFeatures.map(
                  (feature) => feature.properties.remaining_places,
                ),
                filteredFeatures,
              );
              allPlotsDisplayed = true;

              // Deselect on the map
              activeMarkers.forEach((marker) =>
                marker.setStyle({ opacity: 1 }),
              );
            } else {
              // If this item is not selected, select it
              if (currentlySelectedItem) {
                // Deselect the previous item
                currentlySelectedItem.classList.remove("selected");
              }

              // Select the clicked item
              resultItem.classList.add("selected");
              currentlySelectedItem = resultItem;

              // Show only this item's plot
              displayChart(feature, feature.properties["remaining_places"]);
              allPlotsDisplayed = false;

              // Highlight the item on the map by reducing opacity of others
              activeMarkers.forEach((marker) => {
                if (marker !== resultItem.marker) {
                  marker.setStyle({ opacity: 0.3 }); // Dim other markers
                }
              });
            }

            // Center map on marker when result item is clicked
            map.setView([coords[1], coords[0]], 15);
            marker.openPopup();
          });

          resultList.appendChild(resultItem);
        });

        // If no features match the filter, show a message
        if (!resultList.children.length) {
          resultList.innerHTML = "<p>No results found.</p>";
        }

        // Update the plots with filtered data
        const remainingPlacesData = filteredFeatures.map(
          (feature) => feature.properties.remaining_places,
        );

        if (allPlotsDisplayed) {
          displayAllPlots(remainingPlacesData, filteredFeatures);
        }
      }

      // Attach event listeners to checkboxes
      document
        .getElementById("filter-publics")
        .addEventListener("change", filterResults);
      document
        .getElementById("filter-concertats")
        .addEventListener("change", filterResults);
      document
        .getElementById("filter-privats")
        .addEventListener("change", filterResults);

      // Initial render with filters applied
      filterResults();
    });
}

// Update the distance value display and fetch new markers when the range input changes
document
  .getElementById("distance-range")
  .addEventListener("change", function () {
    document.getElementById("distance-value").textContent = this.value;
    if (homeMarker) {
      const { lat, lng } = homeMarker.getLatLng();
      fetchAndDisplayNearbyMarkers(lat, lng);
    }
  });

// Handle map click event
map.on("click", function (e) {
  const { lat, lng } = e.latlng;

  clearMap(); // Clear existing markers, radius circle, area, and home marker

  // Place a home marker at the clicked location
  homeMarker = L.marker([lat, lng], { icon: homeIcon }).addTo(map);

  // Fetch and display nearby markers
  fetchAndDisplayNearbyMarkers(lat, lng);
});
function displayChart(feature, remainingPlaces) {
  const ctx = document.getElementById("remainingPlacesChart").getContext("2d");

  // Destroy the current chart if it exists
  if (currentChart) {
    currentChart.destroy();
  }

  const dates = remainingPlaces.map((item) => item[0]);
  const places = remainingPlaces.map((item) => item[1]);

  // Create a new chart
  currentChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: dates,
      datasets: [
        {
          label: feature.properties.denominaci_completa,
          data: places,
          borderColor: "rgb(75, 192, 192)",
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: {
          type: "category",
          title: {
            display: true,
            text: "Data",
          },
        },
        y: {
          title: {
            display: true,
            text: "Places vacants a I3",
          },
          beginAtZero: true,
        },
      },
    },
  });
}

// Function to update the distance control based on the selected option
function updateDistanceControl() {
  const toggleSwitch = document.getElementById("toggle-switch");
  const distanceRange = document.getElementById("distance-range");
  const distanceValue = document.getElementById("distance-value");
  const filterPrivats = document.getElementById("filter-privats");

  if (toggleSwitch.checked) {
    distanceRange.value = 500;
    distanceRange.disabled = true;
    distanceValue.textContent = 500;
    filterPrivats.checked = false;
    filterPrivats.disabled = true;
  } else {
    distanceRange.disabled = false;
    filterPrivats.disabled = false;
  }
}

// Attach event listener to the toggle switch
document
  .getElementById("toggle-switch")
  .addEventListener("change", function () {
    updateDistanceControl();
    if (homeMarker) {
      const { lat, lng } = homeMarker.getLatLng();
      fetchAndDisplayNearbyMarkers(lat, lng);
    }
  });

// Initial call to set the correct state on page load
updateDistanceControl();

// Handle map click event
map.on("click", function (e) {
  const { lat, lng } = e.latlng;

  clearMap(); // Clear existing markers, radius circle, area, and home marker

  // Place a home marker at the clicked location
  homeMarker = L.marker([lat, lng], { icon: homeIcon }).addTo(map);

  // Fetch and display nearby markers
  fetchAndDisplayNearbyMarkers(lat, lng);
});
