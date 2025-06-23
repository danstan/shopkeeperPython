// Main game interface script
document.addEventListener('DOMContentLoaded', function() {
    document.body.classList.add('js-loaded'); // For testing JS execution

    // --- CONFIG DATA ---
    const allTownsData = window.gameConfig.allTownsDataJson || {};
    const hemlockHerbsData = window.gameConfig.hemlockHerbsData || {};
    const borinItemsData = window.gameConfig.borinItemsData || {};
    const shopData = window.gameConfig.shopData; // Already an object or null
    const shopConfig = window.gameConfig.shopConfig; // Already an object or null
    const playerInventoryForSellDropdown = window.gameConfig.playerInventory || [];


    // --- DOM ELEMENT REFERENCES ---
    // Main Action Form
    const actionForm = document.getElementById('actionForm');
    const hiddenActionNameInput = document.getElementById('action_name_hidden');
    const hiddenDetailsInput = document.getElementById('action_details');

    // Side Info Columns & Panels
    const miniPanels = document.querySelectorAll('.mini-panel');
    const fullPanelContainers = document.querySelectorAll('.full-panel-container');
    const closeFullPanelButtons = document.querySelectorAll('.close-full-panel');

    // Map & Travel
    const mapDestinationsDiv = document.getElementById('map-destinations'); // Inside #travel-actions-container

    // Location Interactions (Bottom Bar - Actions Panel)
    const subLocationsListDiv = document.getElementById('sub-locations-list');
    const currentSubLocationNameDisplay = document.getElementById('current-sub-location-name-display');
    const currentSubLocationActionsListDiv = document.getElementById('current-sub-location-actions-list');
    const currentTownDisplayActions = document.getElementById('current-town-display-actions'); // In Actions Panel

    // Dynamic Action Forms Area (Bottom Bar - Actions Panel)
    const dynamicActionFormsContainer = document.getElementById('dynamic-action-forms-container');
    const allDynamicForms = dynamicActionFormsContainer ? dynamicActionFormsContainer.querySelectorAll('.dynamic-form') : [];
    const closeDynamicFormButtons = dynamicActionFormsContainer ? dynamicActionFormsContainer.querySelectorAll('.close-dynamic-form') : [];

    // Specific Detail Form Elements (Craft, Buy, Sell, NPCs)
    const craftDetailsDiv = document.getElementById('div_craft_details');
    const craftItemNameInput = document.getElementById('craft_item_name');

    const buyDetailsDiv = document.getElementById('div_buy_details');
    const buyItemNameInput = document.getElementById('buy_item_name');
    const buyQuantityInput = document.getElementById('buy_quantity');

    const sellDetailsDiv = document.getElementById('div_sell_details');
    const sellItemNameInput = document.getElementById('sell_item_name');
    const sellItemDropdown = document.getElementById('sell_item_dropdown');

    const hemlockHerbsDetailsDiv = document.getElementById('div_hemlock_herbs_details');
    const hemlockHerbsListDiv = document.getElementById('hemlock-herbs-list');
    const hemlockQuantityInput = document.getElementById('hemlock_quantity_dynamic');
    const submitBuyHemlockHerbButton = document.getElementById('submit_buy_hemlock_herb_button');

    const borinItemsDetailsDiv = document.getElementById('div_borin_items_details');
    const borinItemsListDiv = document.getElementById('borin-items-list'); // Corrected ID
    const borinQuantityInput = document.getElementById('borin_quantity_dynamic');
    const submitBuyBorinItemButton = document.getElementById('submit_buy_borin_item_button');

    const borinRepairDetailsDiv = document.getElementById('div_borin_repair_details');
    const borinRepairItemSelect = document.getElementById('borin-repair-item-select');
    const borinRepairCostDisplay = document.getElementById('borin-repair-cost-display');
    const submitBorinRepairButton = document.getElementById('submit-borin-repair-button');

    // Shop Management (inside full panel)
    const shopManagementDetailsDiv = document.getElementById('shop-management-details');

    // Inventory (Player and Shop, inside full panel)
    const fullInventoryPanel = document.getElementById('full-inventory-panel'); // The content area

    // Bottom Bar Tabs
    const actionsTabButton = document.getElementById('actions-tab-button');
    const logTabButton = document.getElementById('log-tab-button');
    const actionsPanelContent = document.getElementById('actions-panel-content');
    const logPanelContent = document.getElementById('log-panel-content');

    // Top Right Menu
    const topRightMenuButton = document.getElementById('top-right-menu-button');
    const settingsPopup = document.getElementById('settings-popup');
    const settingsOption = document.getElementById('settings-option'); // May not be used if "Settings" is just a label
    const saveGameButton = document.getElementById('save-game-button');

    // General Actions
    const gatherResourcesButton = document.getElementById('gatherResourcesButton');
    // const craftingRecipesList = document.getElementById('crafting-recipes-list'); // If this element still exists and is used.

    // Event Popup
    const eventPopup = document.getElementById('event-choice-popup');


    // --- STATE VARIABLES ---
    let currentOpenDynamicForm = null; // Track which dynamic form (craft, buy, etc.) is open
    let currentSubLocationName = null; // Track selected sub-location for context
    let selectedHemlockHerbName = null;
    let selectedBorinItemName = null;


    // --- HELPER FUNCTIONS ---
    window.showToast = function(message, type = 'info', duration = 5000) {
        const container = document.getElementById('toast-container');
        if (!container) {
            console.error('Toast container not found!');
            return;
        }
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        let iconHtml = '';
        if (type === 'success') iconHtml = '<span class="toast-icon">✔️</span>';
        else if (type === 'error') iconHtml = '<span class="toast-icon">❌</span>';
        else if (type === 'warning') iconHtml = '<span class="toast-icon">⚠️</span>';
        else iconHtml = '<span class="toast-icon">ℹ️</span>';
        toast.innerHTML = `${iconHtml} <span class="toast-message">${message}</span>`;
        container.appendChild(toast);
        setTimeout(() => toast.classList.add('show'), 100);
        setTimeout(() => {
            toast.classList.remove('show');
            toast.addEventListener('transitionend', () => toast.parentElement?.removeChild(toast));
        }, duration);
    };

    function hideAllDynamicForms() {
        if (dynamicActionFormsContainer) dynamicActionFormsContainer.style.display = 'none';
        allDynamicForms.forEach(form => form.style.display = 'none');
        currentOpenDynamicForm = null;
        // Make other action sections visible again if they were hidden
        document.getElementById('travel-actions-container').style.display = 'block';
        document.getElementById('location-interactions-container').style.display = 'block';
        document.getElementById('general-actions-container').style.display = 'block';

    }

    function showDynamicForm(formElement) {
        hideAllDynamicForms(); // Hide any currently open form
        if (formElement) {
            // Hide other action sections to focus on the form
            document.getElementById('travel-actions-container').style.display = 'none';
            document.getElementById('location-interactions-container').style.display = 'none';
            document.getElementById('general-actions-container').style.display = 'none';

            if (dynamicActionFormsContainer) dynamicActionFormsContainer.style.display = 'block';
            formElement.style.display = 'block';
            currentOpenDynamicForm = formElement;
            formElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        } else {
             // If no form to show, ensure main action sections are visible
            document.getElementById('travel-actions-container').style.display = 'block';
            document.getElementById('location-interactions-container').style.display = 'block';
            document.getElementById('general-actions-container').style.display = 'block';
        }
    }


    // --- INITIALIZATION FUNCTIONS ---

    function initializeSidePanelInteractions() {
        miniPanels.forEach(miniPanel => {
            const fullPanelId = miniPanel.getAttribute('aria-controls');
            const fullPanelContainer = document.getElementById(fullPanelId);

            if (fullPanelContainer) {
                miniPanel.addEventListener('click', () => {
                    fullPanelContainer.style.display = 'flex'; // Show the panel
                    miniPanel.setAttribute('aria-expanded', 'true');
                });
                miniPanel.addEventListener('keydown', (event) => { // Keyboard accessibility
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        fullPanelContainer.style.display = 'flex';
                        miniPanel.setAttribute('aria-expanded', 'true');
                    }
                });
            }
        });

        closeFullPanelButtons.forEach(button => {
            button.addEventListener('click', () => {
                const fullPanelContainer = button.closest('.full-panel-container');
                if (fullPanelContainer) {
                    fullPanelContainer.style.display = 'none'; // Hide the panel
                    // Find the corresponding mini-panel to update aria-expanded
                    const miniPanel = document.querySelector(`[aria-controls="${fullPanelContainer.id}"]`);
                    if (miniPanel) {
                        miniPanel.setAttribute('aria-expanded', 'false');
                    }
                }
            });
        });

        // Clicking outside the full-panel-content should also close it
        fullPanelContainers.forEach(container => {
            container.addEventListener('click', function(event) {
                if (event.target === container) { // Only if the click is on the overlay itself
                    container.style.display = 'none';
                    const miniPanel = document.querySelector(`[aria-controls="${container.id}"]`);
                    if (miniPanel) {
                        miniPanel.setAttribute('aria-expanded', 'false');
                    }
                }
            });
        });
    }

    function initializeBottomBarTabs() {
        if (actionsTabButton && logTabButton && actionsPanelContent && logPanelContent) {
            actionsTabButton.addEventListener('click', () => {
                actionsPanelContent.style.display = 'block'; // Use .panel-visible class if preferred
                actionsPanelContent.classList.add('panel-visible');
                logPanelContent.style.display = 'none';
                logPanelContent.classList.remove('panel-visible');

                actionsTabButton.classList.add('active-tab-button');
                logTabButton.classList.remove('active-tab-button');
                actionsTabButton.setAttribute('aria-selected', 'true');
                logTabButton.setAttribute('aria-selected', 'false');
            });

            logTabButton.addEventListener('click', () => {
                logPanelContent.style.display = 'block';
                logPanelContent.classList.add('panel-visible');
                actionsPanelContent.style.display = 'none';
                actionsPanelContent.classList.remove('panel-visible');

                logTabButton.classList.add('active-tab-button');
                actionsTabButton.classList.remove('active-tab-button');
                logTabButton.setAttribute('aria-selected', 'true');
                actionsTabButton.setAttribute('aria-selected', 'false');
            });

            // Initial state: Actions tab is active
            actionsTabButton.click(); // Simulate a click to set initial state
        }
    }

    function initializeSellFunctionality() {
        function populateSellDropdown() {
            if (!sellItemDropdown || !playerInventoryForSellDropdown) return;
            sellItemDropdown.innerHTML = '<option value="">-- Select an item to sell --</option>';
            playerInventoryForSellDropdown.forEach(item => {
                const option = document.createElement('option');
                const itemName = (typeof item === 'string') ? item : (item && item.name);
                if (!itemName) return;
                option.value = itemName;
                option.textContent = itemName;
                sellItemDropdown.appendChild(option);
            });
        }

        if (sellItemDropdown && sellItemNameInput) {
            sellItemDropdown.addEventListener('change', function() {
                if (this.value && sellItemNameInput) {
                    sellItemNameInput.value = this.value;
                }
            });
        }
        if (sellItemDropdown) populateSellDropdown(); // Initial population
    }

    function initializeCoreGameActions() {
        function displaySubLocations() {
            if (!subLocationsListDiv || !currentTownDisplayActions) return;
            subLocationsListDiv.innerHTML = ''; // Clear previous sub-locations
            if (currentSubLocationActionsListDiv) currentSubLocationActionsListDiv.innerHTML = ''; // Clear previous actions
            if (currentSubLocationNameDisplay) currentSubLocationNameDisplay.style.display = 'none'; // Hide name display
            hideAllDynamicForms();

            const currentTownName = currentTownDisplayActions.textContent;
            const townData = allTownsData[currentTownName];

            if (townData && townData.sub_locations && townData.sub_locations.length > 0) {
                const ul = document.createElement('ul');
                ul.className = 'button-list'; // Use the new class for styling
                townData.sub_locations.forEach(subLoc => {
                    const li = document.createElement('li');
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'action-button sub-location-button'; // General action button style
                    button.dataset.sublocName = subLoc.name;
                    button.textContent = subLoc.name;
                    li.appendChild(button);
                    // Optional: Add description if needed, though might clutter
                    // if (subLoc.description) li.append(` - ${subLoc.description}`);
                    ul.appendChild(li);
                });
                subLocationsListDiv.appendChild(ul);
            } else {
                subLocationsListDiv.innerHTML = '<p>No sub-locations here.</p>';
            }
        }

        function displaySubLocationActions(subLocName) {
            if (!currentSubLocationActionsListDiv || !currentSubLocationNameDisplay) return;
            currentSubLocationActionsListDiv.innerHTML = ''; // Clear previous actions
            hideAllDynamicForms();

            currentSubLocationName = subLocName;
            currentSubLocationNameDisplay.textContent = subLocName;
            currentSubLocationNameDisplay.style.display = 'block';

            const currentTownName = currentTownDisplayActions.textContent;
            const townData = allTownsData[currentTownName];
            const selectedSubLocation = townData?.sub_locations?.find(sl => sl.name === subLocName);

            if (selectedSubLocation && selectedSubLocation.actions && selectedSubLocation.actions.length > 0) {
                const ul = document.createElement('ul');
                ul.className = 'button-list';
                selectedSubLocation.actions.forEach(actionStr => {
                    const li = document.createElement('li');
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'action-button subloc-action-button'; // Specific class if needed
                    button.dataset.actionName = actionStr;
                    button.textContent = actionStr.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    li.appendChild(button);
                    ul.appendChild(li);
                });
                currentSubLocationActionsListDiv.appendChild(ul);
            } else {
                currentSubLocationActionsListDiv.innerHTML = '<p>No actions available here.</p>';
            }
        }

        // Event listener for sub-location buttons
        if (subLocationsListDiv) {
            subLocationsListDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('sub-location-button')) {
                    const subLocName = event.target.dataset.sublocName;
                    displaySubLocationActions(subLocName);
                }
            });
        }

        // Event listener for actions within a selected sub-location
        if (currentSubLocationActionsListDiv) {
            currentSubLocationActionsListDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('subloc-action-button')) { // Or general 'action-button'
                    handleActionClick(event.target.dataset.actionName, event.target);
                }
            });
        }

        // Event listener for map destination buttons
        if (mapDestinationsDiv) {
            mapDestinationsDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('map-destination-button')) {
                    const townName = event.target.dataset.townName;
                    if (hiddenActionNameInput) hiddenActionNameInput.value = 'travel_to_town';
                    if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({ town_name: townName });
                    if (actionForm) actionForm.submit();
                }
            });
        }

        // Event listener for general action buttons (like Gather Resources)
        if (gatherResourcesButton) {
            gatherResourcesButton.addEventListener('click', function() {
                handleActionClick('gather_resources', gatherResourcesButton);
            });
        }

        // Centralized handler for most action initiations
        function handleActionClick(actionName, buttonElement) {
            if (hiddenActionNameInput) hiddenActionNameInput.value = actionName;
            // currentSubLocationName is already set if this is a sub-location action

            // Logic to show specific forms based on actionName
            if (actionName === 'craft') {
                showDynamicForm(craftDetailsDiv);
            } else if (actionName === 'buy_from_own_shop') {
                showDynamicForm(buyDetailsDiv);
            } else if (actionName === 'sell_to_own_shop') {
                populateSellDropdown();
                showDynamicForm(sellDetailsDiv);
            } else if (actionName === 'buy_from_npc' && currentSubLocationName === "Old Man Hemlock's Hut") {
                selectedHemlockHerbName = null; // Reset selection
                if (hemlockHerbsListDiv) {
                    hemlockHerbsListDiv.innerHTML = ''; // Clear previous list
                    if (hemlockHerbsData && Object.keys(hemlockHerbsData).length > 0) {
                        const ul = document.createElement('ul');
                        ul.style.listStyleType = 'none'; ul.style.paddingLeft = '0';
                        for (const herbKey in hemlockHerbsData) {
                            const herb = hemlockHerbsData[herbKey];
                            const li = document.createElement('li');
                            li.style.marginBottom = '10px';
                            li.innerHTML = `<strong>${herb.name}</strong> - ${herb.price}G<br><em>${herb.description}</em><br><button type="button" class="action-button select-hemlock-herb-button" data-herb-name="${herb.name}">Select</button>`;
                            ul.appendChild(li);
                        }
                        hemlockHerbsListDiv.appendChild(ul);
                    } else {
                        hemlockHerbsListDiv.innerHTML = '<p>No herbs available from Hemlock.</p>';
                    }
                }
                showDynamicForm(hemlockHerbsDetailsDiv);
            } else if ((actionName === 'talk_to_borin' || actionName === 'buy_from_npc') && currentSubLocationName === "Borin Stonebeard's Smithy") {
                 // Assuming 'talk_to_borin' might lead to buy options. If 'buy_from_npc' is a direct action here:
                selectedBorinItemName = null; // Reset selection
                if (borinItemsListDiv) { // Ensure this is the correct ID from HTML
                    borinItemsListDiv.innerHTML = ''; // Clear previous list
                    if (borinItemsData && Object.keys(borinItemsData).length > 0) {
                        const ul = document.createElement('ul');
                        ul.style.listStyleType = 'none'; ul.style.paddingLeft = '0';
                        for (const itemKey in borinItemsData) {
                            const item = borinItemsData[itemKey];
                            const li = document.createElement('li');
                            li.style.marginBottom = '10px';
                            li.innerHTML = `<strong>${item.name}</strong> - ${item.price}G<br><em>${item.description}</em><br><button type="button" class="action-button select-borin-item-button" data-item-name="${item.name}">Select</button>`;
                            ul.appendChild(li);
                        }
                        borinItemsListDiv.appendChild(ul);
                    } else {
                        borinItemsListDiv.innerHTML = '<p>Borin has nothing to sell right now.</p>';
                    }
                }
                showDynamicForm(borinItemsDetailsDiv);
            } else if (actionName === 'repair_gear_borin' && currentSubLocationName === "Borin Stonebeard's Smithy") {
                if (borinRepairItemSelect) {
                    borinRepairItemSelect.innerHTML = '<option value="">-- Select Item --</option>';
                    if (window.gameConfig.playerInventory && window.gameConfig.playerInventory.length > 0) {
                        window.gameConfig.playerInventory.forEach(item => {
                            const itemName = (typeof item === 'string') ? item : item.name;
                            if(itemName) {
                                const option = document.createElement('option');
                                option.value = itemName;
                                option.textContent = itemName;
                                borinRepairItemSelect.appendChild(option);
                            }
                        });
                    } else {
                         borinRepairItemSelect.innerHTML = '<option value="">-- No items to repair --</option>';
                    }
                    borinRepairItemSelect.onchange = function() {
                        if(borinRepairCostDisplay) borinRepairCostDisplay.textContent = this.value ? "Cost determined by Borin" : "N/A";
                    };
                    if(borinRepairCostDisplay) borinRepairCostDisplay.textContent = "N/A";
                }
                showDynamicForm(borinRepairDetailsDiv);
            } else {
                // Action does not require a dynamic form, submit directly
                if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({}); // Empty details
                if (actionForm) {
                    if (buttonElement) buttonElement.classList.add('button-processing');
                    actionForm.submit();
                }
            }
        }

        // Event listeners for "Select" buttons within NPC forms
        if (hemlockHerbsListDiv) {
            hemlockHerbsListDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('select-hemlock-herb-button')) {
                    selectedHemlockHerbName = event.target.dataset.herbName;
                    hemlockHerbsListDiv.querySelectorAll('.select-hemlock-herb-button').forEach(btn => {
                        btn.style.fontWeight = 'normal'; btn.style.backgroundColor = ''; // Reset others
                    });
                    event.target.style.fontWeight = 'bold'; event.target.style.backgroundColor = '#a0d2a0'; // Highlight selected
                }
            });
        }
        if (borinItemsListDiv) {
            borinItemsListDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('select-borin-item-button')) {
                    selectedBorinItemName = event.target.dataset.itemName;
                     borinItemsListDiv.querySelectorAll('.select-borin-item-button').forEach(btn => {
                        btn.style.fontWeight = 'normal'; btn.style.backgroundColor = ''; // Reset others
                    });
                    event.target.style.fontWeight = 'bold'; event.target.style.backgroundColor = '#a0d2a0'; // Highlight selected
                }
            });
        }


        // Event listeners for SUBMIT buttons within each dynamic form
        // This uses event delegation on the dynamicActionFormsContainer for submit buttons
        if (dynamicActionFormsContainer) {
            dynamicActionFormsContainer.addEventListener('click', function(event) {
                const targetButton = event.target.closest('.submit-details-button, #submit_buy_hemlock_herb_button, #submit_buy_borin_item_button, #submit-borin-repair-button');
                if (!targetButton) return;

                let details = {};
                let actionName = hiddenActionNameInput.value; // Should be set by handleActionClick

                if (currentOpenDynamicForm === craftDetailsDiv) {
                    if (craftItemNameInput && craftItemNameInput.value) details.item_name = craftItemNameInput.value;
                    actionName = 'craft'; // Ensure action name is correct
                } else if (currentOpenDynamicForm === buyDetailsDiv) {
                    if (buyItemNameInput && buyItemNameInput.value) details.item_name = buyItemNameInput.value;
                    if (buyQuantityInput && buyQuantityInput.value) details.quantity = parseInt(buyQuantityInput.value, 10);
                    actionName = 'buy_from_own_shop';
                } else if (currentOpenDynamicForm === sellDetailsDiv) {
                    if (sellItemNameInput && sellItemNameInput.value) details.item_name = sellItemNameInput.value;
                    // sellItemDropdown value is already in sellItemNameInput via its own change listener
                    actionName = 'sell_to_own_shop';
                } else if (currentOpenDynamicForm === hemlockHerbsDetailsDiv) {
                    if (!selectedHemlockHerbName) { showToast("Please select an herb to buy.", "warning"); return; }
                    const quantity = parseInt(hemlockQuantityInput.value, 10);
                    if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity.", "warning"); return; }
                    details = { npc_name: "Old Man Hemlock", item_name: selectedHemlockHerbName, quantity: quantity };
                    actionName = 'buy_from_npc';
                } else if (currentOpenDynamicForm === borinItemsDetailsDiv) {
                    if (!selectedBorinItemName) { showToast("Please select an item to buy from Borin.", "warning"); return; }
                    const quantity = parseInt(borinQuantityInput.value, 10);
                    if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity.", "warning"); return; }
                    details = { npc_name: "Borin Stonebeard", item_name: selectedBorinItemName, quantity: quantity };
                    actionName = 'buy_from_npc';
                } else if (currentOpenDynamicForm === borinRepairDetailsDiv) {
                    const selectedItemToRepair = borinRepairItemSelect ? borinRepairItemSelect.value : null;
                    if (!selectedItemToRepair) { showToast("Please select an item to repair.", "warning"); return; }
                    details = { item_name_to_repair: selectedItemToRepair };
                    actionName = 'repair_gear_borin';
                }

                if (hiddenActionNameInput) hiddenActionNameInput.value = actionName;
                if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify(details);
                if (actionForm) {
                    targetButton.classList.add('button-processing');
                    actionForm.submit();
                }
            });
        }

        // Add listeners for close buttons on dynamic forms
        closeDynamicFormButtons.forEach(button => {
            button.addEventListener('click', () => {
                hideAllDynamicForms();
                // Optionally, re-display sub-locations if that was the previous state
                if (currentTownDisplayActions && currentTownDisplayActions.textContent) {
                     displaySubLocations(); // Re-render sub-locations for the current town
                }
            });
        });

        // Initial population of sub-locations
        if (currentTownDisplayActions && currentTownDisplayActions.textContent) {
            displaySubLocations();
        } else {
            if(subLocationsListDiv) subLocationsListDiv.innerHTML = '<p>No town context.</p>';
        }
    } // End of initializeCoreGameActions

    function initializeShopManagementInterface() {
        // This function now assumes it's populating content within a full-panel
        // The #shop-management-details div is inside #full-shop-mgt-panel
        function populateShopManagementUI() {
            if (!shopManagementDetailsDiv || !shopData || !shopConfig) {
                if(shopManagementDetailsDiv) shopManagementDetailsDiv.innerHTML = '<p>Shop data not available.</p>';
                return;
            }
            // ... (rest of the shop UI population logic remains the same) ...
             let html = `<h3>${shopData.name}</h3>`; // HTML already has H2, so use H3 or P
            html += `<p>Level: ${shopData.level} (Quality Bonus: +${shopData.current_quality_bonus})</p>`;
            html += `<p>Specialization: ${shopData.specialization}</p>`;
            html += `<p>Inventory: ${shopData.inventory_count} / ${shopData.max_inventory_slots} slots</p>`;
            html += `<p>Player Gold: ${window.gameConfig.playerGold !== undefined ? window.gameConfig.playerGold : 'N/A'}</p>`;

            html += `<h4>Change Specialization</h4><select id="shop-specialization-select" class="themed-select">`;
            shopConfig.specialization_types.forEach(specType => {
                html += `<option value="${specType}" ${shopData.specialization === specType ? 'selected' : ''}>${specType.replace(/_/g, ' ')}</option>`;
            });
            html += `</select><button type="button" id="submit-change-specialization" class="action-button">Set Specialization</button>`;

            html += `<h4>Upgrade Shop</h4>`;
            if (shopData.max_level_reached) {
                html += `<p>Shop is at maximum level (${shopConfig.max_shop_level}).</p>`;
            } else {
                html += `<p>Next Level: ${shopData.level + 1}</p><p>Cost: ${shopData.next_level_cost} Gold</p>`;
                html += `<p>Max Inventory Slots: ${shopData.next_level_slots}</p><p>Crafting Quality Bonus: +${shopData.next_level_quality_bonus}</p>`;
                html += `<button type="button" id="submit-upgrade-shop" class="action-button">Upgrade Shop</button>`;
            }
            shopManagementDetailsDiv.innerHTML = html;

            const changeSpecButton = document.getElementById('submit-change-specialization');
            if (changeSpecButton && actionForm && hiddenActionNameInput && hiddenDetailsInput) {
                changeSpecButton.addEventListener('click', function() {
                    const selectElement = document.getElementById('shop-specialization-select');
                    hiddenActionNameInput.value = 'set_shop_specialization';
                    hiddenDetailsInput.value = JSON.stringify({ specialization_name: selectElement.value });
                    actionForm.submit();
                });
            }
            const upgradeShopButton = document.getElementById('submit-upgrade-shop');
            if (upgradeShopButton && actionForm && hiddenActionNameInput && hiddenDetailsInput) {
                upgradeShopButton.addEventListener('click', function() {
                    hiddenActionNameInput.value = 'upgrade_shop';
                    hiddenDetailsInput.value = JSON.stringify({});
                    actionForm.submit();
                });
            }
        }
        // Populate if data is available (e.g., when its full panel is opened, or on load if always available)
        if (shopManagementDetailsDiv && shopData) { // Check shopData as well
            populateShopManagementUI();
        }
    }

    function initializeShopBuyButtonFunctionality() {
        // This listener is on the #full-inventory-panel which contains the shop items.
        if (fullInventoryPanel && buyItemNameInput && buyDetailsDiv) {
            fullInventoryPanel.addEventListener('click', function(event) {
                if (event.target.classList.contains('buy-item-button')) {
                    const itemName = event.target.dataset.itemName;
                    if (buyItemNameInput) buyItemNameInput.value = itemName;

                    // Close the inventory full panel
                    const inventoryFullPanel = document.getElementById('full-inventory-panel-container');
                    if (inventoryFullPanel) inventoryFullPanel.style.display = 'none';
                     const miniInvPanel = document.getElementById('mini-inventory-panel');
                    if(miniInvPanel) miniInvPanel.setAttribute('aria-expanded', 'false');


                    // Switch to Actions tab and show the buy form
                    if (actionsTabButton) actionsTabButton.click(); // Activate actions tab
                    showDynamicForm(buyDetailsDiv); // Show the buy form
                    if (buyItemNameInput) buyItemNameInput.focus();
                }
            });
        }
    }

    function initializeTopRightMenu() {
        if (topRightMenuButton && settingsPopup) {
            topRightMenuButton.addEventListener('click', (event) => {
                event.stopPropagation(); // Prevent click from immediately closing via document listener
                const isHidden = settingsPopup.style.display === 'none' || settingsPopup.style.display === '';
                settingsPopup.style.display = isHidden ? 'block' : 'none';
                topRightMenuButton.setAttribute('aria-expanded', isHidden.toString());
            });
        }
        // Settings option might be just a header or future functionality.
        // if (settingsOption) {
        //     settingsOption.addEventListener('click', () => {
        //         showToast("Settings panel coming soon!", "info");
        //         if (settingsPopup) settingsPopup.style.display = 'none';
        //         topRightMenuButton.setAttribute('aria-expanded', 'false');
        //     });
        // }
        if (saveGameButton) {
            saveGameButton.addEventListener('click', function() {
                showToast("Game progress is automatically saved after each action.", "info", 7000);
                if (settingsPopup) settingsPopup.style.display = 'none';
                if (topRightMenuButton) topRightMenuButton.setAttribute('aria-expanded', 'false');
            });
        }
        // Close popup if clicking outside
        document.addEventListener('click', function(event) {
            if (settingsPopup && settingsPopup.style.display === 'block') {
                if (!settingsPopup.contains(event.target) && !topRightMenuButton.contains(event.target)) {
                    settingsPopup.style.display = 'none';
                    if (topRightMenuButton) topRightMenuButton.setAttribute('aria-expanded', 'false');
                }
            }
        });
    }

    function processInitialGameDataPopups() {
        const popupActionResult = window.gameConfig.popupActionResult;
        if (popupActionResult && popupActionResult.trim() !== "") {
            const toastMessage = popupActionResult.replace(/<br\s*\/?>/gi, " ");
            let actionResultType = 'info';
            if (toastMessage.toLowerCase().includes('success')) actionResultType = 'success';
            else if (toastMessage.toLowerCase().includes('fail') || toastMessage.toLowerCase().includes('error') || toastMessage.toLowerCase().includes('not possible')) actionResultType = 'error';
            else if (toastMessage.toLowerCase().includes('warning')) actionResultType = 'warning';
            showToast(toastMessage, actionResultType, 7000);
        }

        const awaitingEventChoice = window.gameConfig.awaitingEventChoice;
        const pendingEventDataJson = window.gameConfig.pendingEventDataJson;
        if (awaitingEventChoice && pendingEventDataJson && eventPopup) {
            try {
                const eventData = pendingEventDataJson; // Already an object
                const eventPopupNameEl = document.getElementById('event-popup-name');
                const eventPopupDescriptionEl = document.getElementById('event-popup-description');
                const choicesContainer = document.getElementById('event-popup-choices');

                if (eventPopupNameEl) eventPopupNameEl.textContent = eventData.name || "An Event Occurs!";
                if (eventPopupDescriptionEl) eventPopupDescriptionEl.innerHTML = eventData.description || "You must make a choice."; // Use innerHTML if desc can have HTML

                if (choicesContainer) {
                    choicesContainer.innerHTML = ''; // Clear previous choices
                    if (eventData.choices && eventData.choices.length > 0) {
                        eventData.choices.forEach(function(choice, index) {
                            const button = document.createElement('button');
                            button.className = 'event-choice-button action-button'; // Themed button
                            button.dataset.choiceIndex = index;
                            let buttonText = choice.text;
                            if (choice.skill && choice.dc) buttonText += ` <span class="skill-check-indicator">[${choice.skill} DC ${choice.dc}]</span>`;
                            if (choice.item_requirement_desc) buttonText += ` <span class="item-req-indicator">(${choice.item_requirement_desc})</span>`;
                            button.innerHTML = buttonText; // Use innerHTML for spans
                            choicesContainer.appendChild(button);
                        });
                        // Add event listener to choices container (delegation)
                         if (!choicesContainer.dataset.listenerAttached) { // Prevent multiple listeners
                            choicesContainer.addEventListener('click', function(event) {
                                if (event.target.classList.contains('event-choice-button')) {
                                    const choiceIndex = event.target.dataset.choiceIndex;
                                    const currentEventName = eventData.name; // Or get from a data attribute if eventData changes scope

                                    if (choiceIndex === undefined || !currentEventName) {
                                        console.error("Error: Missing choice index or event name.");
                                        showToast("Error processing your choice.", "error");
                                        return;
                                    }
                                    // Submit choice via a dynamically created form
                                    const form = document.createElement('form');
                                    form.method = 'POST';
                                    form.action = window.gameConfig.submitEventChoiceUrl; // URL from gameConfig
                                    const eventNameInput = document.createElement('input');
                                    eventNameInput.type = 'hidden'; eventNameInput.name = 'event_name'; eventNameInput.value = currentEventName;
                                    form.appendChild(eventNameInput);
                                    const choiceIndexInput = document.createElement('input');
                                    choiceIndexInput.type = 'hidden'; choiceIndexInput.name = 'choice_index'; choiceIndexInput.value = choiceIndex;
                                    form.appendChild(choiceIndexInput);
                                    document.body.appendChild(form);
                                    form.submit();
                                    if (eventPopup) eventPopup.style.display = 'none';
                                }
                            });
                            choicesContainer.dataset.listenerAttached = 'true';
                        }
                    } else {
                        choicesContainer.innerHTML = '<p>No choices available for this event.</p>';
                    }
                }
                if (eventPopup) eventPopup.style.display = 'block'; // Show the modal
            } catch (e) {
                console.error("Error processing event data for popup:", e);
                if (eventPopup) eventPopup.style.display = 'none';
            }
        }

        const lastSkillRollStr = window.gameConfig.lastSkillRollStr;
        if (lastSkillRollStr && lastSkillRollStr.trim() !== "") {
            let skillRollType = 'info';
            if (lastSkillRollStr.toLowerCase().includes('success')) skillRollType = 'success';
            else if (lastSkillRollStr.toLowerCase().includes('fail') || lastSkillRollStr.toLowerCase().includes('failure')) skillRollType = 'error';
            showToast(lastSkillRollStr, skillRollType, 7000);
        }
    }

    // --- EXECUTE INITIALIZERS ---
    initializeSidePanelInteractions();
    initializeBottomBarTabs();
    initializeTopRightMenu();

    if (actionForm) { // Core game actions only if logged in and character selected
        initializeCoreGameActions();
        initializeSellFunctionality(); // Depends on sellItemDropdown created in HTML
        initializeShopBuyButtonFunctionality(); // Depends on inventory items being present
    }

    if (shopManagementDetailsDiv && shopData) { // Shop management if data exists
        initializeShopManagementInterface();
    }

    processInitialGameDataPopups(); // Toasts for results, event popups

    // Final check: Ensure the default view is correct (e.g., Actions tab visible)
    if (actionsTabButton) {
        // actionsTabButton.click(); // This is now handled in initializeBottomBarTabs
    }
});
