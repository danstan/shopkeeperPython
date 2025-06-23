// Main game interface script
document.addEventListener('DOMContentLoaded', function() {
    // Phase 1: Moved global-like variables into DOMContentLoaded
    document.body.classList.add('js-loaded'); // Add class to body for testing JS execution
    const currentTownSubLocations = window.gameConfig.currentTownSubLocationsJson;
    const allTownsData = window.gameConfig.allTownsDataJson;

    // Directly assign data from window.gameConfig, assuming it's already a JS object or {}
    const hemlockHerbsData = window.gameConfig.hemlockHerbsData || {};
    const borinItemsData = window.gameConfig.borinItemsData || {};

    const shopData = window.gameConfig.shopData;
    const shopConfig = window.gameConfig.shopConfig;
    const shopManagementDetailsDiv = document.getElementById('shop-management-details');
    if (!shopManagementDetailsDiv) {
        console.warn("Shop management details div not found on page load.");
    }

    const playerInventoryForSellDropdown = window.gameConfig.playerInventory;

    // DOM Element Constants (most frequently used)
    const actionForm = document.getElementById('actionForm');
    const hiddenActionNameInput = document.getElementById('action_name_hidden');
    const hiddenDetailsInput = document.getElementById('action_details');
    const mapDestinationsDiv = document.getElementById('map-destinations');
    const subLocationsListDiv = document.getElementById('sub-locations-list');
    const currentActionsListDiv = document.getElementById('current-actions-list'); // Still used for an event listener
    const currentTownDisplay = document.getElementById('current-town-display');
    const subLocationActionsModal = document.getElementById('subLocationActionsModal');
    const modalActionsListDiv = document.getElementById('modal-actions-list');
    const modalCloseButton = subLocationActionsModal ? subLocationActionsModal.querySelector('.close-button') : null;
    const actionDetailsContainer = document.getElementById('action-details-container');
    const craftDetailsDiv = document.getElementById('div_craft_details');
    const craftItemNameInput = document.getElementById('craft_item_name');
    const buyDetailsDiv = document.getElementById('div_buy_details');
    const buyItemNameInput = document.getElementById('buy_item_name');
    const buyQuantityInput = document.getElementById('buy_quantity');
    const sellDetailsDiv = document.getElementById('div_sell_details');
    const sellItemNameInput = document.getElementById('sell_item_name');
    const hemlockHerbsDetailsDiv = document.getElementById('div_hemlock_herbs_details');
    const hemlockHerbsListDiv = document.getElementById('hemlock-herbs-list');
    const borinItemsDetailsDiv = document.getElementById('div_borin_items_details');
    const borinRepairDetailsDiv = document.getElementById('div_borin_repair_details');
    const allDetailDivs = [craftDetailsDiv, buyDetailsDiv, sellDetailsDiv, hemlockHerbsDetailsDiv, borinItemsDetailsDiv, borinRepairDetailsDiv];
    const inventoryContent = document.getElementById('inventory-content');
    const actionsTabButton = document.getElementById('actions-tab-button');
    const logTabButton = document.getElementById('log-tab-button');
    const actionsPanelContent = document.getElementById('actions-panel-content');
    const logPanelContent = document.getElementById('log-panel-content');
    const topRightMenuButton = document.getElementById('top-right-menu-button');
    const settingsPopup = document.getElementById('settings-popup');
    const settingsOption = document.getElementById('settings-option');
    const saveGameButton = document.getElementById('save-game-button');
    const craftingRecipesList = document.getElementById('crafting-recipes-list');
    const gatherResourcesButton = document.getElementById('gatherResourcesButton');
    const eventPopup = document.getElementById('event-choice-popup');
    const sellItemDropdown = document.getElementById('sell_item_dropdown'); // Moved up for initializeSellFunctionality

    let currentActionRequiringDetails = null;
    let currentSubLocationName = null;
    let selectedHemlockHerbName = null;
    let selectedBorinItemName = null;

    // Phase 2: Function Extraction

    function initializeToastNotifications() {
        // showToast is defined in this scope, effectively making it available to other functions in DOMContentLoaded
        window.showToast = function(message, type = 'info', duration = 5000) { // Assign to window to make it globally accessible if needed by external scripts, otherwise keep as const
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
    }

    function initializeSellFunctionality() {
        function populateSellDropdown() {
            if (!sellItemDropdown || !playerInventoryForSellDropdown) return;
            sellItemDropdown.innerHTML = '<option value="">-- Select an item to sell --</option>';
            playerInventoryForSellDropdown.forEach(item => {
                const option = document.createElement('option');
                let itemName = (typeof item === 'string') ? item : (item && item.name);
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
        function hideAllDetailForms() {
            if (actionDetailsContainer) actionDetailsContainer.style.display = 'none';
            allDetailDivs.forEach(div => { if (div) div.style.display = 'none'; });
        }

        function displaySubLocations(subLocations) {
            if (!subLocationsListDiv) return;
            subLocationsListDiv.innerHTML = '';
            if (currentActionsListDiv) currentActionsListDiv.innerHTML = ''; // This might be modalActionsListDiv now
            hideAllDetailForms();

            if (subLocations && subLocations.length > 0) {
                const ul = document.createElement('ul');
                subLocations.forEach(subLoc => {
                    const li = document.createElement('li');
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'sub-location-button';
                    button.dataset.sublocName = subLoc.name;
                    button.textContent = subLoc.name;
                    li.appendChild(button);
                    if (subLoc.description) li.append(` - ${subLoc.description}`);
                    ul.appendChild(li);
                });
                subLocationsListDiv.appendChild(ul);
            } else {
                subLocationsListDiv.innerHTML = '<p>No sub-locations here.</p>';
            }
        }

        function displayActions(subLocName) {
            if (!modalActionsListDiv || !subLocationActionsModal) {
                console.error("Modal elements not found for displayActions");
                return;
            }
            modalActionsListDiv.innerHTML = '';
            currentSubLocationName = subLocName;

            const currentTownName = currentTownDisplay ? currentTownDisplay.textContent : null;
            if (!currentTownName || !allTownsData || !allTownsData[currentTownName] || !allTownsData[currentTownName].sub_locations) {
                console.error("Could not find current town data or sub-locations for action display.");
                modalActionsListDiv.innerHTML = '<p>Error: Town data missing.</p>';
                subLocationActionsModal.style.display = 'block';
                return;
            }
            const subLocationsData = allTownsData[currentTownName].sub_locations;
            const selectedSubLocation = subLocationsData.find(sl => sl.name === subLocName);

            if (selectedSubLocation && selectedSubLocation.actions && selectedSubLocation.actions.length > 0) {
                const ul = document.createElement('ul');
                selectedSubLocation.actions.forEach(actionStr => {
                    const li = document.createElement('li');
                    const button = document.createElement('button');
                    button.className = 'action-button';
                    button.dataset.actionName = actionStr;
                    button.textContent = actionStr.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                    li.appendChild(button);
                    ul.appendChild(li);
                });
                modalActionsListDiv.appendChild(ul);
            } else {
                modalActionsListDiv.innerHTML = '<p>No actions available here.</p>';
            }
            subLocationActionsModal.style.display = 'block';
        }

        const actionButtonClickHandler = function(event) {
            if (event.target.classList.contains('action-button')) {
                const actionName = event.target.dataset.actionName;
                if (subLocationActionsModal && subLocationActionsModal.contains(event.target)) {
                    subLocationActionsModal.style.display = 'none';
                }
                hideAllDetailForms();
                currentActionRequiringDetails = null;

                if (hiddenActionNameInput) hiddenActionNameInput.value = actionName;

                if (actionName === 'craft' && !event.target.classList.contains('craft-recipe-button')) {
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    if (craftDetailsDiv) craftDetailsDiv.style.display = 'block';
                    currentActionRequiringDetails = actionName;
                } else if (actionName === 'buy_from_own_shop') {
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    if (buyDetailsDiv) buyDetailsDiv.style.display = 'block';
                    currentActionRequiringDetails = actionName;
                } else if (actionName === 'sell_to_own_shop') {
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    if (sellDetailsDiv) sellDetailsDiv.style.display = 'block';
                    currentActionRequiringDetails = actionName;
                    if (typeof populateSellDropdown === 'function') populateSellDropdown(); // Ensure it's populated
                } else if (actionName === 'buy_from_npc' && currentSubLocationName === "Old Man Hemlock's Hut") {
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    if (hemlockHerbsDetailsDiv) hemlockHerbsDetailsDiv.style.display = 'block';
                    currentActionRequiringDetails = actionName;
                    selectedHemlockHerbName = null;
                    if (hemlockHerbsListDiv) {
                        hemlockHerbsListDiv.innerHTML = '';
                        if (hemlockHerbsData && Object.keys(hemlockHerbsData).length > 0) {
                            const ul = document.createElement('ul');
                            ul.style.listStyleType = 'none'; ul.style.paddingLeft = '0';
                            for (const herbKey in hemlockHerbsData) {
                                const herb = hemlockHerbsData[herbKey];
                                const li = document.createElement('li');
                                li.style.marginBottom = '10px';
                                li.innerHTML = `<strong>${herb.name}</strong> - ${herb.price}G<br><em>${herb.description}</em><br><button type="button" class="select-hemlock-herb-button popup-menu-button" data-herb-name="${herb.name}">Select</button>`;
                                ul.appendChild(li);
                            }
                            hemlockHerbsListDiv.appendChild(ul);
                        } else {
                            hemlockHerbsListDiv.innerHTML = '<p>No herbs available from Hemlock at this time.</p>';
                        }
                    }
                } else if (actionName === 'talk_to_borin' && currentSubLocationName === "Borin Stonebeard's Smithy") {
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    if (borinItemsDetailsDiv) borinItemsDetailsDiv.style.display = 'block';
                    currentActionRequiringDetails = 'buy_from_borin_ui';
                    selectedBorinItemName = null;
                    const localBorinItemsListDiv = document.getElementById('borin-items-list');
                    if (localBorinItemsListDiv) {
                        localBorinItemsListDiv.innerHTML = '';
                        if (borinItemsData && Object.keys(borinItemsData).length > 0) {
                            const ul = document.createElement('ul');
                            ul.style.listStyleType = 'none'; ul.style.paddingLeft = '0';
                            for (const itemKey in borinItemsData) {
                                const item = borinItemsData[itemKey];
                                const li = document.createElement('li');
                                li.style.marginBottom = '10px';
                                li.innerHTML = `<strong>${item.name}</strong> - ${item.price}G<br><em>${item.description}</em><br><button type="button" class="select-borin-item-button popup-menu-button" data-item-name="${item.name}">Select</button>`;
                                ul.appendChild(li);
                            }
                            localBorinItemsListDiv.appendChild(ul);
                        } else {
                            localBorinItemsListDiv.innerHTML = '<p>Borin has nothing to sell right now.</p>';
                        }
                    }
                } else if (actionName === 'repair_gear_borin' && currentSubLocationName === "Borin Stonebeard's Smithy") {
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    if (borinRepairDetailsDiv) borinRepairDetailsDiv.style.display = 'block';
                    currentActionRequiringDetails = 'repair_gear_borin_ui';
                    const repairItemSelect = document.getElementById('borin-repair-item-select');
                    const repairCostDisplay = document.getElementById('borin-repair-cost-display');
                    if (repairItemSelect) {
                        repairItemSelect.innerHTML = '<option value="">-- Select Item --</option>';
                        if (window.gameConfig && window.gameConfig.playerInventory && window.gameConfig.playerInventory.length > 0) {
                            window.gameConfig.playerInventory.forEach(item => {
                                const itemName = (typeof item === 'string') ? item : item.name;
                                if(itemName) {
                                    const option = document.createElement('option');
                                    option.value = itemName;
                                    option.textContent = itemName;
                                    repairItemSelect.appendChild(option);
                                }
                            });
                        } else {
                            repairItemSelect.innerHTML = '<option value="">-- No items in inventory --</option>';
                        }
                        repairItemSelect.onchange = function() {
                            if(repairCostDisplay) repairCostDisplay.textContent = this.value ? "Cost determined by Borin" : "N/A";
                        };
                        if(repairCostDisplay) repairCostDisplay.textContent = "N/A";
                    }
                } else if (!event.target.classList.contains('craft-recipe-button')) {
                    if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({});
                    if (actionForm) {
                        if (event.target && typeof event.target.classList !== 'undefined') event.target.classList.add('button-processing');
                        actionForm.submit();
                    }
                }
            }
        };

        function compileAndSetActionDetails() {
            let details = {};
            if (!currentActionRequiringDetails) return;
            switch (currentActionRequiringDetails) {
                case 'craft':
                    if (craftItemNameInput && craftItemNameInput.value) details.item_name = craftItemNameInput.value;
                    break;
                case 'buy_from_own_shop':
                    if (buyItemNameInput && buyItemNameInput.value) details.item_name = buyItemNameInput.value;
                    if (buyQuantityInput && buyQuantityInput.value) details.quantity = parseInt(buyQuantityInput.value, 10);
                    break;
                case 'sell_to_own_shop':
                    if (sellItemNameInput && sellItemNameInput.value) details.item_name = sellItemNameInput.value;
                    break;
            }
            if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify(details);
        }

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

        if (subLocationsListDiv) {
            subLocationsListDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('sub-location-button')) {
                    const subLocName = event.target.dataset.sublocName;
                    displayActions(subLocName);
                }
            });
        }

        if (modalActionsListDiv) modalActionsListDiv.addEventListener('click', actionButtonClickHandler);
        if (currentActionsListDiv) currentActionsListDiv.addEventListener('click', actionButtonClickHandler); // Kept if it handles other buttons

        if (actionDetailsContainer) {
            actionDetailsContainer.addEventListener('click', function(event) {
                if (event.target.classList.contains('submit-details-button')) {
                    if (!currentActionRequiringDetails) return;
                    if (hiddenActionNameInput &&
                        (currentActionRequiringDetails === 'buy_from_own_shop' || currentActionRequiringDetails === 'sell_to_own_shop' || currentActionRequiringDetails === 'craft')) {
                        hiddenActionNameInput.value = currentActionRequiringDetails;
                    }
                    compileAndSetActionDetails();
                    if (actionForm) {
                        if (event.target && typeof event.target.classList !== 'undefined') event.target.classList.add('button-processing');
                        actionForm.submit();
                    }
                }
            });
        }

        if (hemlockHerbsListDiv) {
            hemlockHerbsListDiv.addEventListener('click', function(event) {
                if (event.target.classList.contains('select-hemlock-herb-button')) {
                    selectedHemlockHerbName = event.target.dataset.herbName;
                    document.querySelectorAll('.select-hemlock-herb-button').forEach(btn => { btn.style.fontWeight = 'normal'; btn.style.backgroundColor = ''; });
                    event.target.style.fontWeight = 'bold'; event.target.style.backgroundColor = '#a0d2a0';
                }
            });
        }

        const submitBuyHemlockHerbButton = document.getElementById('submit_buy_hemlock_herb_button');
        const hemlockQuantityInput = document.getElementById('hemlock_quantity_dynamic');
        if (submitBuyHemlockHerbButton && hemlockQuantityInput && hiddenActionNameInput && hiddenDetailsInput && actionForm) {
            submitBuyHemlockHerbButton.addEventListener('click', function() {
                if (!selectedHemlockHerbName) { alert("Please select an herb to buy."); return; }
                const quantity = parseInt(hemlockQuantityInput.value, 10);
                if (isNaN(quantity) || quantity < 1) { alert("Please enter a valid quantity (at least 1)."); return; }
                hiddenActionNameInput.value = 'buy_from_npc';
                hiddenDetailsInput.value = JSON.stringify({ npc_name: "Old Man Hemlock", item_name: selectedHemlockHerbName, quantity: quantity });
                if (submitBuyHemlockHerbButton) submitBuyHemlockHerbButton.classList.add('button-processing');
                actionForm.submit();
            });
        }

        const borinItemsListDivLocal = document.getElementById('borin-items-list');
        if (borinItemsListDivLocal) {
            borinItemsListDivLocal.addEventListener('click', function(event) {
                if (event.target.classList.contains('select-borin-item-button')) {
                    selectedBorinItemName = event.target.dataset.itemName;
                    document.querySelectorAll('.select-borin-item-button').forEach(btn => { btn.style.fontWeight = 'normal'; btn.style.backgroundColor = ''; });
                    event.target.style.fontWeight = 'bold'; event.target.style.backgroundColor = '#a0d2a0';
                }
            });
        }

        const submitBuyBorinItemButton = document.getElementById('submit_buy_borin_item_button');
        const borinQuantityInput = document.getElementById('borin_quantity_dynamic');
        if (submitBuyBorinItemButton && borinQuantityInput && hiddenActionNameInput && hiddenDetailsInput && actionForm) {
            submitBuyBorinItemButton.addEventListener('click', function() {
                if (!selectedBorinItemName) { showToast("Please select an item to buy from Borin.", "warning"); return; }
                const quantity = parseInt(borinQuantityInput.value, 10);
                if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity (at least 1).", "warning"); return; }
                hiddenActionNameInput.value = 'buy_from_npc';
                hiddenDetailsInput.value = JSON.stringify({ npc_name: "Borin Stonebeard", item_name: selectedBorinItemName, quantity: quantity });
                submitBuyBorinItemButton.classList.add('button-processing');
                actionForm.submit();
            });
        }

        const submitBorinRepairButton = document.getElementById('submit-borin-repair-button');
        if (submitBorinRepairButton && hiddenActionNameInput && hiddenDetailsInput && actionForm) {
            submitBorinRepairButton.addEventListener('click', function() {
                const repairItemSelect = document.getElementById('borin-repair-item-select');
                const selectedItemName = repairItemSelect ? repairItemSelect.value : null;
                if (!selectedItemName) { showToast("Please select an item to repair.", "warning"); return; }
                hiddenActionNameInput.value = 'repair_gear_borin';
                hiddenDetailsInput.value = JSON.stringify({ item_name_to_repair: selectedItemName });
                submitBorinRepairButton.classList.add('button-processing');
                actionForm.submit();
            });
        }

        if (craftingRecipesList) {
            craftingRecipesList.addEventListener('click', function(event) {
                if (event.target.classList.contains('craft-recipe-button')) {
                    const itemName = event.target.dataset.itemName;
                    if (hiddenActionNameInput) hiddenActionNameInput.value = 'craft';
                    if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({ item_name: itemName });
                    if (actionForm) actionForm.submit();
                }
            });
        }

        if (gatherResourcesButton) {
            gatherResourcesButton.addEventListener('click', function() {
                if (hiddenActionNameInput) hiddenActionNameInput.value = 'gather_resources';
                if (hiddenDetailsInput) hiddenDetailsInput.value = JSON.stringify({});
                if (actionForm) actionForm.submit();
            });
        }

        if (currentTownDisplay && currentTownDisplay.textContent && allTownsData && allTownsData[currentTownDisplay.textContent]) {
            const currentTownData = allTownsData[currentTownDisplay.textContent];
            if (currentTownData && currentTownData.sub_locations) displaySubLocations(currentTownData.sub_locations);
            else displaySubLocations([]);
        } else {
            displaySubLocations([]);
        }
    } // End of initializeCoreGameActions

    function initializeShopManagementInterface() {
        function populateShopManagementUI() {
            if (!shopManagementDetailsDiv || !shopData || !shopConfig) {
                if(shopManagementDetailsDiv) shopManagementDetailsDiv.innerHTML = '<p>Shop data not available.</p>';
                return;
            }
            let html = `<h3>${shopData.name}</h3>`;
            html += `<p>Level: ${shopData.level} (Quality Bonus: +${shopData.current_quality_bonus})</p>`;
            html += `<p>Specialization: ${shopData.specialization}</p>`;
            html += `<p>Inventory: ${shopData.inventory_count} / ${shopData.max_inventory_slots} slots</p>`;
            html += `<p>Player Gold: ${window.gameConfig.playerGold !== undefined ? window.gameConfig.playerGold : 'N/A'}</p>`;
            html += `<h4>Change Specialization</h4><select id="shop-specialization-select">`;
            shopConfig.specialization_types.forEach(specType => {
                html += `<option value="${specType}" ${shopData.specialization === specType ? 'selected' : ''}>${specType}</option>`;
            });
            html += `</select><button type="button" id="submit-change-specialization" class="popup-menu-button">Set Specialization</button>`;
            html += `<h4>Upgrade Shop</h4>`;
            if (shopData.max_level_reached) {
                html += `<p>Shop is at maximum level (${shopConfig.max_shop_level}).</p>`;
            } else {
                html += `<p>Next Level: ${shopData.level + 1}</p><p>Cost: ${shopData.next_level_cost} Gold</p>`;
                html += `<p>Max Inventory Slots: ${shopData.next_level_slots}</p><p>Crafting Quality Bonus: +${shopData.next_level_quality_bonus}</p>`;
                html += `<button type="button" id="submit-upgrade-shop" class="popup-menu-button">Upgrade Shop</button>`;
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
        if(shopManagementDetailsDiv) populateShopManagementUI();
    }

    function initializeShopBuyButtonFunctionality() {
        if (inventoryContent && buyItemNameInput && buyDetailsDiv) {
            inventoryContent.addEventListener('click', function(event) {
                if (event.target.classList.contains('buy-item-button')) {
                    const itemName = event.target.dataset.itemName;
                    buyItemNameInput.value = itemName;
                    if (actionsTabButton) actionsTabButton.click();
                    if (actionDetailsContainer) actionDetailsContainer.style.display = 'block';
                    allDetailDivs.forEach(div => { if (div) div.style.display = 'none'; });
                    if (buyDetailsDiv) buyDetailsDiv.style.display = 'block';
                    buyDetailsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    buyItemNameInput.focus();
                }
            });
        } else {
            if (!inventoryContent) console.warn("Inventory content not found, cannot attach buy button listener.");
            if (!buyItemNameInput) console.warn("Buy item name input not found for buy button listener dependency.");
            if (!buyDetailsDiv) console.warn("Buy details div not found for buy button listener dependency.");
        }
    }

    function initializeMainInterfaceInteractions() {
        document.body.classList.add('init-main-interface-called'); // DEBUG MARKER RESTORED HERE
        if (actionsTabButton && actionsPanelContent && logTabButton && logPanelContent) {
            actionsTabButton.addEventListener('click', () => {
                actionsPanelContent.classList.add('panel-visible');
                logPanelContent.classList.remove('panel-visible');
                actionsTabButton.classList.add('active-tab-button');
                logTabButton.classList.remove('active-tab-button');
            });
            logTabButton.addEventListener('click', () => {
                logPanelContent.classList.add('panel-visible');
                actionsPanelContent.classList.remove('panel-visible');
                logTabButton.classList.add('active-tab-button');
                actionsTabButton.classList.remove('active-tab-button');
            });
            actionsTabButton.classList.add('active-tab-button'); // Default
            actionsPanelContent.classList.add('panel-visible'); // Default
                if (actionsPanelContent) actionsPanelContent.classList.add('actions-panel-initialized'); // Ensure this is present
                if (actionsTabButton) actionsTabButton.classList.add('actions-tab-button-initialized'); // New debug marker
                // Ensure log tab is not active/visible initially
            logTabButton.classList.remove('active-tab-button');
            logPanelContent.classList.remove('panel-visible');
        }

        if (topRightMenuButton && settingsPopup) {
            topRightMenuButton.addEventListener('click', () => {
                settingsPopup.style.display = settingsPopup.style.display === 'none' || settingsPopup.style.display === '' ? 'block' : 'none';
            });
        }
        if (settingsOption) { // This element's specific logic might be minimal now
            settingsOption.addEventListener('click', () => {
                console.log("Settings option clicked (now likely just a placeholder).");
                if (settingsPopup) settingsPopup.style.display = 'none';
            });
        }
        if (saveGameButton) {
            saveGameButton.addEventListener('click', function() {
                if (typeof showToast === 'function') showToast("Game progress is automatically saved after each action.", "info", 7000);
                else alert("Game progress is automatically saved after each action.");
                if (settingsPopup) settingsPopup.style.display = 'none';
            });
        }
        document.addEventListener('click', function(event) {
            if (settingsPopup && topRightMenuButton && settingsPopup.style.display === 'block' &&
                !topRightMenuButton.contains(event.target) && !settingsPopup.contains(event.target)) {
                settingsPopup.style.display = 'none';
            }
        });

        const actionsTabContainer = document.getElementById('actions-tab');
        document.addEventListener('click', function(event) {
            const isActionsPanelVisible = actionsPanelContent && actionsPanelContent.classList.contains('panel-visible');
            const isLogPanelVisible = logPanelContent && logPanelContent.classList.contains('panel-visible');
            if ((isActionsPanelVisible || isLogPanelVisible) && actionsTabContainer && !actionsTabContainer.contains(event.target)) {
                if (actionsPanelContent) actionsPanelContent.classList.remove('panel-visible');
                if (logPanelContent) logPanelContent.classList.remove('panel-visible');
                if (actionsTabButton) actionsTabButton.classList.remove('active-tab-button');
                if (logTabButton) logTabButton.classList.remove('active-tab-button');
            }
        });
    }

    function initializeModalFunctionality() {
        if (modalCloseButton && subLocationActionsModal) {
            modalCloseButton.addEventListener('click', () => subLocationActionsModal.style.display = 'none');
        }
        if (subLocationActionsModal) {
            subLocationActionsModal.addEventListener('click', function(event) {
                if (event.target === subLocationActionsModal) subLocationActionsModal.style.display = 'none';
            });
        }
    }

    function processInitialGameDataPopups() {
        const popupActionResult = window.gameConfig.popupActionResult;
        if (popupActionResult && popupActionResult.trim() !== "") {
            const toastMessage = popupActionResult.replace(/<br\s*\/?>/gi, " ");
            let actionResultType = 'info';
            if (toastMessage.toLowerCase().includes('success')) actionResultType = 'success';
            else if (toastMessage.toLowerCase().includes('fail') || toastMessage.toLowerCase().includes('error') || toastMessage.toLowerCase().includes('not possible')) actionResultType = 'error';
            else if (toastMessage.toLowerCase().includes('warning')) actionResultType = 'warning';
            if (typeof showToast === 'function') showToast(toastMessage, actionResultType, 7000);
        }

        const awaitingEventChoice = window.gameConfig.awaitingEventChoice;
        const pendingEventDataJson = window.gameConfig.pendingEventDataJson; // Already an object or null
        if (awaitingEventChoice && pendingEventDataJson && eventPopup) {
            try {
                const eventData = pendingEventDataJson;
                const eventPopupNameEl = document.getElementById('event-popup-name');
                const eventPopupDescriptionEl = document.getElementById('event-popup-description');
                const choicesContainer = document.getElementById('event-popup-choices');

                if (eventPopupNameEl) eventPopupNameEl.textContent = eventData.name || "An Event Occurs!";
                if (eventPopupDescriptionEl) eventPopupDescriptionEl.textContent = eventData.description || "You must make a choice.";

                if (choicesContainer) {
                    choicesContainer.innerHTML = '';
                    if (eventData.choices && eventData.choices.length > 0) {
                        eventData.choices.forEach(function(choice, index) {
                            const button = document.createElement('button');
                            button.className = 'event-choice-button button';
                            button.dataset.choiceIndex = index;
                            let buttonText = choice.text;
                            if (choice.skill && choice.dc) buttonText += ` [${choice.skill} DC ${choice.dc}]`;
                            if (choice.item_requirement_desc) buttonText += ` (${choice.item_requirement_desc})`;
                            button.textContent = buttonText;
                            choicesContainer.appendChild(button);
                        });
                        choicesContainer.addEventListener('click', function(event) { // Moved listener here
                            if (event.target.classList.contains('event-choice-button')) {
                                const choiceIndex = event.target.dataset.choiceIndex;
                                const currentEventName = eventData.name;
                                if (choiceIndex === undefined || !currentEventName) {
                                    console.error("Error: Missing choice index or event name for submission.");
                                    alert("Error processing your choice. Please try again.");
                                    return;
                                }
                                const form = document.createElement('form');
                                form.method = 'POST';
                                form.action = window.gameConfig.submitEventChoiceUrl;
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
                        }, { once: true }); // Add listener once choices are populated
                    } else {
                        choicesContainer.innerHTML = '<p>No choices available for this event.</p>';
                    }
                }
                eventPopup.style.display = 'block';
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
            if (typeof showToast === 'function') showToast(lastSkillRollStr, skillRollType, 7000);
        }
    }

    // Phase 3: Calling Initializer Functions
    initializeToastNotifications();
    initializeModalFunctionality();
    initializeMainInterfaceInteractions();
    // Only initialize core game actions if the main form exists (i.e., user is logged in and past char creation/selection)
    if (actionForm) {
        initializeCoreGameActions();
        initializeSellFunctionality(); // Depends on elements within core game actions
        initializeShopBuyButtonFunctionality(); // May depend on actions tab
    }
    if (shopManagementDetailsDiv) { // Only if the shop management div exists
        initializeShopManagementInterface();
    }
    processInitialGameDataPopups();
});
