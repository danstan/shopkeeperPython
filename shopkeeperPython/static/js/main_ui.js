// Main game interface script

// --- CONSTANTS ---
const CONSTANTS = {
    ACTION_NAMES: {
        TRAVEL_TO_TOWN: 'travel_to_town',
        CRAFT: 'craft',
        BUY_FROM_OWN_SHOP: 'buy_from_own_shop',
        SELL_TO_OWN_SHOP: 'sell_to_own_shop',
        BUY_FROM_NPC: 'buy_from_npc',
        TALK_TO_BORIN: 'talk_to_borin', // Might be combined with BUY_FROM_NPC logic
        REPAIR_GEAR_BORIN: 'repair_gear_borin',
        GATHER_RESOURCES: 'gather_resources',
        STUDY_LOCAL_HISTORY: 'study_local_history',
        ORGANIZE_INVENTORY: 'organize_inventory',
        POST_ADVERTISEMENTS: 'post_advertisements',
        REST_SHORT: 'rest_short',
        REST_LONG: 'rest_long',
        SET_SHOP_SPECIALIZATION: 'set_shop_specialization',
        UPGRADE_SHOP: 'upgrade_shop',
    },
    NPC_NAMES: {
        HEMLOCK: "Old Man Hemlock",
        BORIN: "Borin Stonebeard",
    },
    SUB_LOCATIONS: {
        HEMLOCK_HUT: "Old Man Hemlock's Hut",
        BORIN_SMITHY: "Borin Stonebeard's Smithy",
    }
};

// --- GLOBAL STATE (scoped within this IIFE if script becomes a module) ---
let currentOpenDynamicForm = null;
let currentSubLocationName = null;
let selectedHemlockHerbName = null;
let selectedBorinItemName = null;

// --- DOM ELEMENT REFERENCES (grouped by functionality) ---
// Populated in `cacheDomElements`
const DOM = {};

function cacheDomElements() {
    // Main Action Form
    DOM.actionForm = document.getElementById('actionForm');
    DOM.hiddenActionNameInput = document.getElementById('action_name_hidden');
    DOM.hiddenDetailsInput = document.getElementById('action_details');

    // Side Info Columns & Panels
    DOM.miniPanels = document.querySelectorAll('.mini-panel');
    DOM.fullPanelContainers = document.querySelectorAll('.full-panel-container');
    DOM.closeFullPanelButtons = document.querySelectorAll('.close-full-panel');

    // Map & Travel
    DOM.mapDestinationsDiv = document.getElementById('map-destinations');

    // Location Interactions (Bottom Bar - Actions Panel)
    DOM.subLocationsListDiv = document.getElementById('sub-locations-list');
    DOM.currentSubLocationNameDisplay = document.getElementById('current-sub-location-name-display');
    DOM.currentSubLocationActionsListDiv = document.getElementById('current-sub-location-actions-list');
    DOM.currentTownDisplayActions = document.getElementById('current-town-display-actions');

    // Dynamic Action Forms Area (Bottom Bar - Actions Panel)
    DOM.dynamicActionFormsContainer = document.getElementById('dynamic-action-forms-container');
    DOM.allDynamicForms = DOM.dynamicActionFormsContainer ? DOM.dynamicActionFormsContainer.querySelectorAll('.dynamic-form') : [];
    DOM.closeDynamicFormButtons = DOM.dynamicActionFormsContainer ? DOM.dynamicActionFormsContainer.querySelectorAll('.close-dynamic-form') : [];
    DOM.travelActionsContainer = document.getElementById('travel-actions-container');
    DOM.locationInteractionsContainer = document.getElementById('location-interactions-container');
    DOM.generalActionsContainer = document.getElementById('general-actions-container');


    // Specific Detail Form Elements
    DOM.craftDetailsDiv = document.getElementById('div_craft_details');
    DOM.craftItemNameInput = document.getElementById('craft_item_name');

    DOM.buyDetailsDiv = document.getElementById('div_buy_details');
    DOM.buyItemNameInput = document.getElementById('buy_item_name');
    DOM.buyQuantityInput = document.getElementById('buy_quantity');

    DOM.sellDetailsDiv = document.getElementById('div_sell_details');
    DOM.sellItemNameInput = document.getElementById('sell_item_name');
    DOM.sellItemDropdown = document.getElementById('sell_item_dropdown');

    // Hemlock (NPC)
    DOM.hemlockHerbsDetailsDiv = document.getElementById('div_hemlock_herbs_details');
    DOM.hemlockHerbsListDiv = document.getElementById('hemlock-herbs-list');
    DOM.hemlockQuantityInput = document.getElementById('hemlock_quantity_dynamic');
    // DOM.submitBuyHemlockHerbButton = document.getElementById('submit_buy_hemlock_herb_button'); // Covered by delegation

    // Borin (NPC)
    DOM.borinItemsDetailsDiv = document.getElementById('div_borin_items_details');
    DOM.borinItemsListDiv = document.getElementById('borin-items-list');
    DOM.borinQuantityInput = document.getElementById('borin_quantity_dynamic');
    // DOM.submitBuyBorinItemButton = document.getElementById('submit_buy_borin_item_button'); // Covered by delegation
    DOM.borinRepairDetailsDiv = document.getElementById('div_borin_repair_details');
    DOM.borinRepairItemSelect = document.getElementById('borin-repair-item-select');
    DOM.borinRepairCostDisplay = document.getElementById('borin-repair-cost-display');
    // DOM.submitBorinRepairButton = document.getElementById('submit-borin-repair-button'); // Covered by delegation

    // Shop Management
    DOM.shopManagementDetailsDiv = document.getElementById('shop-management-details');
    DOM.fullShopMgtPanelContainer = document.getElementById('full-shop-mgt-panel-container'); // Assuming this is the outer container
    DOM.miniShopMgtPanel = document.getElementById('mini-shop-mgt-panel'); // Assuming this is the trigger

    // Inventory
    DOM.fullInventoryPanel = document.getElementById('full-inventory-panel'); // Content area
    DOM.fullInventoryPanelContainer = document.getElementById('full-inventory-panel-container');
    DOM.miniInventoryPanel = document.getElementById('mini-inventory-panel');


    // Bottom Bar Tabs
    DOM.actionsTabButton = document.getElementById('actions-tab-button');
    DOM.logTabButton = document.getElementById('log-tab-button');
    DOM.actionsPanelContent = document.getElementById('actions-panel-content');
    DOM.logPanelContent = document.getElementById('log-panel-content');

    // Top Right Menu
    DOM.topRightMenuButton = document.getElementById('top-right-menu-button');
    DOM.settingsPopup = document.getElementById('settings-popup');
    // DOM.settingsOption = document.getElementById('settings-option'); // Potentially unused
    DOM.saveGameButton = document.getElementById('save-game-button');

    // General Action Buttons
    DOM.gatherResourcesButton = document.getElementById('gatherResourcesButton');
    DOM.studyLocalHistoryButton = document.getElementById('studyLocalHistoryButton');
    DOM.organizeInventoryButton = document.getElementById('organizeInventoryButton');
    DOM.postAdvertisementsButton = document.getElementById('postAdvertisementsButton');
    DOM.shortRestButton = document.getElementById('shortRestButton');
    DOM.longRestButton = document.getElementById('longRestButton');

    // Event Popup
    DOM.eventPopup = document.getElementById('event-choice-popup');
    DOM.eventPopupNameEl = document.getElementById('event-popup-name');
    DOM.eventPopupDescriptionEl = document.getElementById('event-popup-description');
    DOM.eventPopupChoicesContainer = document.getElementById('event-popup-choices');

    // Toast Container
    DOM.toastContainer = document.getElementById('toast-container');
}


// --- CONFIG DATA (scoped) ---
let gameConfigData = {};
function loadConfigData() {
    gameConfigData.allTownsData = window.gameConfig.allTownsDataJson || {};
    gameConfigData.hemlockHerbsData = window.gameConfig.hemlockHerbsData || {};
    gameConfigData.borinItemsData = window.gameConfig.borinItemsData || {};
    gameConfigData.shopData = window.gameConfig.shopData;
    gameConfigData.shopConfig = window.gameConfig.shopConfig;
    gameConfigData.playerInventoryForSellDropdown = window.gameConfig.playerInventory || [];
    gameConfigData.playerGold = window.gameConfig.playerGold;
    gameConfigData.popupActionResult = window.gameConfig.popupActionResult;
    gameConfigData.awaitingEventChoice = window.gameConfig.awaitingEventChoice;
    gameConfigData.pendingEventDataJson = window.gameConfig.pendingEventDataJson;
    gameConfigData.lastSkillRollStr = window.gameConfig.lastSkillRollStr;
    gameConfigData.submitEventChoiceUrl = window.gameConfig.submitEventChoiceUrl;

}


// --- HELPER FUNCTIONS ---
function showToast(message, type = 'info', duration = 5000) {
    if (!DOM.toastContainer) {
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
    DOM.toastContainer.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 100); // Delay for CSS transition
    setTimeout(() => {
        toast.classList.remove('show');
        toast.addEventListener('transitionend', () => toast.parentElement?.removeChild(toast));
    }, duration);
}
// Make showToast globally accessible if needed by other scripts or inline event handlers (though ideally not)
window.showToast = showToast;


function hideAllDynamicForms() {
    if (DOM.dynamicActionFormsContainer) DOM.dynamicActionFormsContainer.style.display = 'none';
    if (DOM.allDynamicForms) DOM.allDynamicForms.forEach(form => form.style.display = 'none');
    currentOpenDynamicForm = null;

    // Make other action sections visible again
    if (DOM.travelActionsContainer) DOM.travelActionsContainer.style.display = 'block';
    if (DOM.locationInteractionsContainer) DOM.locationInteractionsContainer.style.display = 'block';
    if (DOM.generalActionsContainer) DOM.generalActionsContainer.style.display = 'block';
}

function showDynamicForm(formElement) {
    hideAllDynamicForms(); // Hide any currently open form
    if (formElement) {
        // Hide other action sections to focus on the form
        if (DOM.travelActionsContainer) DOM.travelActionsContainer.style.display = 'none';
        if (DOM.locationInteractionsContainer) DOM.locationInteractionsContainer.style.display = 'none';
        if (DOM.generalActionsContainer) DOM.generalActionsContainer.style.display = 'none';

        if (DOM.dynamicActionFormsContainer) DOM.dynamicActionFormsContainer.style.display = 'block';
        formElement.style.display = 'block';
        currentOpenDynamicForm = formElement;
        formElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    } else {
        // If no form to show, ensure main action sections are visible (handled by hideAllDynamicForms)
    }
}


// --- INITIALIZATION MODULES ---

const UIPanels = {
    init() {
        if (!DOM.miniPanels || !DOM.closeFullPanelButtons || !DOM.fullPanelContainers) return;

        DOM.miniPanels.forEach(miniPanel => {
            const fullPanelId = miniPanel.getAttribute('aria-controls');
            const fullPanelContainer = document.getElementById(fullPanelId);

            if (fullPanelContainer) {
                const openPanel = () => {
                    // Hide all other full panels first
                    DOM.fullPanelContainers.forEach(p => {
                        if (p !== fullPanelContainer) {
                            p.classList.add('hidden');
                            const correspondingMiniPanel = document.querySelector(`[aria-controls="${p.id}"]`);
                            if (correspondingMiniPanel) {
                                correspondingMiniPanel.setAttribute('aria-expanded', 'false');
                            }
                        }
                    });
                    fullPanelContainer.classList.remove('hidden');
                    miniPanel.setAttribute('aria-expanded', 'true');
                };
                miniPanel.addEventListener('click', openPanel);
                miniPanel.addEventListener('keydown', (event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        openPanel();
                    }
                });
            }
        });

        DOM.closeFullPanelButtons.forEach(button => {
            button.addEventListener('click', () => {
                const fullPanelContainer = button.closest('.full-panel-container');
                if (fullPanelContainer) {
                    fullPanelContainer.classList.add('hidden');
                    const miniPanel = document.querySelector(`[aria-controls="${fullPanelContainer.id}"]`);
                    if (miniPanel) miniPanel.setAttribute('aria-expanded', 'false');
                }
            });
        });

        DOM.fullPanelContainers.forEach(container => {
            container.addEventListener('click', function(event) {
                if (event.target === container) { // Click on overlay, not content
                    container.classList.add('hidden');
                    const miniPanel = document.querySelector(`[aria-controls="${container.id}"]`);
                    if (miniPanel) miniPanel.setAttribute('aria-expanded', 'false');
                }
            });
        });
    }
};

const UIBottomTabs = {
    init() {
        if (!DOM.actionsTabButton || !DOM.logTabButton || !DOM.actionsPanelContent || !DOM.logPanelContent) return;

        const switchTab = (activeTab, inactiveTab, activePanel, inactivePanel) => {
            activePanel.style.display = 'block';
            activePanel.classList.add('panel-visible');
            inactivePanel.style.display = 'none';
            inactivePanel.classList.remove('panel-visible');

            activeTab.classList.add('active-tab-button');
            inactiveTab.classList.remove('active-tab-button');
            activeTab.setAttribute('aria-selected', 'true');
            inactiveTab.setAttribute('aria-selected', 'false');
        };

        DOM.actionsTabButton.addEventListener('click', () => {
            switchTab(DOM.actionsTabButton, DOM.logTabButton, DOM.actionsPanelContent, DOM.logPanelContent);
        });

        DOM.logTabButton.addEventListener('click', () => {
            switchTab(DOM.logTabButton, DOM.actionsTabButton, DOM.logPanelContent, DOM.actionsPanelContent);
        });

        // Initial state: Actions tab is active
        DOM.actionsTabButton.click();
    }
};

const UIShopAndInventory = {
    populateSellDropdown() {
        if (!DOM.sellItemDropdown || !gameConfigData.playerInventoryForSellDropdown) return;
        DOM.sellItemDropdown.innerHTML = '<option value="">-- Select an item to sell --</option>';
        gameConfigData.playerInventoryForSellDropdown.forEach(item => {
            const option = document.createElement('option');
            const itemName = (typeof item === 'string') ? item : (item && item.name);
            if (!itemName) return;
            option.value = itemName;
            option.textContent = itemName; // Consider adding quantity if available: e.g., `${itemName} (x${item.quantity})`
            DOM.sellItemDropdown.appendChild(option);
        });
    },

    initSellFunctionality() {
        if (DOM.sellItemDropdown && DOM.sellItemNameInput) {
            DOM.sellItemDropdown.addEventListener('change', function() {
                if (this.value && DOM.sellItemNameInput) {
                    DOM.sellItemNameInput.value = this.value;
                }
            });
        }
        if (DOM.sellItemDropdown) this.populateSellDropdown();
    },

    initShopBuyButtonFunctionality() {
        if (DOM.fullInventoryPanel && DOM.buyItemNameInput && DOM.buyDetailsDiv) {
            DOM.fullInventoryPanel.addEventListener('click', (event) => {
                if (event.target.classList.contains('buy-item-button')) {
                    const itemName = event.target.dataset.itemName;
                    if (DOM.buyItemNameInput) DOM.buyItemNameInput.value = itemName;

                    if (DOM.fullInventoryPanelContainer) DOM.fullInventoryPanelContainer.style.display = 'none';
                    if (DOM.miniInventoryPanel) DOM.miniInventoryPanel.setAttribute('aria-expanded', 'false');

                    if (DOM.actionsTabButton) DOM.actionsTabButton.click();
                    showDynamicForm(DOM.buyDetailsDiv);
                    if (DOM.buyItemNameInput) DOM.buyItemNameInput.focus();
                }
            });
        }
    },

    populateShopManagementUI() {
        if (!DOM.shopManagementDetailsDiv || !gameConfigData.shopData || !gameConfigData.shopConfig) {
            if (DOM.shopManagementDetailsDiv) DOM.shopManagementDetailsDiv.innerHTML = '<p>Shop data not available.</p>';
            return;
        }
        const { shopData, shopConfig, playerGold } = gameConfigData;
        let html = `<h3>${shopData.name}</h3>`;
        html += `<p>Level: ${shopData.level} (Quality Bonus: +${shopData.current_quality_bonus})</p>`;
        html += `<p>Specialization: ${shopData.specialization}</p>`;
        html += `<p>Inventory: ${shopData.inventory_count} / ${shopData.max_inventory_slots} slots</p>`;
        html += `<p>Player Gold: ${playerGold !== undefined ? playerGold : 'N/A'}</p>`;

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
        DOM.shopManagementDetailsDiv.innerHTML = html;

        // Re-attach event listeners after innerHTML overwrite
        this.attachShopManagementActionListeners();
    },

    attachShopManagementActionListeners() {
        const changeSpecButton = document.getElementById('submit-change-specialization');
        if (changeSpecButton && DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
            changeSpecButton.addEventListener('click', () => {
                const selectElement = document.getElementById('shop-specialization-select');
                DOM.hiddenActionNameInput.value = CONSTANTS.ACTION_NAMES.SET_SHOP_SPECIALIZATION;
                DOM.hiddenDetailsInput.value = JSON.stringify({ specialization_name: selectElement.value });
                DOM.actionForm.submit();
            });
        }
        const upgradeShopButton = document.getElementById('submit-upgrade-shop');
        if (upgradeShopButton && DOM.actionForm && DOM.hiddenActionNameInput && DOM.hiddenDetailsInput) {
            upgradeShopButton.addEventListener('click', () => {
                DOM.hiddenActionNameInput.value = CONSTANTS.ACTION_NAMES.UPGRADE_SHOP;
                DOM.hiddenDetailsInput.value = JSON.stringify({});
                DOM.actionForm.submit();
            });
        }
    },

    initShopManagementInterface() {
        if (DOM.shopManagementDetailsDiv && gameConfigData.shopData) {
            this.populateShopManagementUI();
            // If the panel is opened dynamically, populateShopManagementUI should be called then.
            // For now, assuming it might be visible on load or its content is prepped.
        }
    },

    init() {
        this.initSellFunctionality();
        this.initShopBuyButtonFunctionality();
        this.initShopManagementInterface();
    }
};


const UIActionsAndEvents = {
    displaySubLocations() {
        if (!DOM.subLocationsListDiv || !DOM.currentTownDisplayActions) return;
        DOM.subLocationsListDiv.innerHTML = '';
        if (DOM.currentSubLocationActionsListDiv) DOM.currentSubLocationActionsListDiv.innerHTML = '';
        if (DOM.currentSubLocationNameDisplay) DOM.currentSubLocationNameDisplay.style.display = 'none';
        hideAllDynamicForms();

        const currentTownName = DOM.currentTownDisplayActions.textContent;
        const townData = gameConfigData.allTownsData[currentTownName];

        if (townData && townData.sub_locations && townData.sub_locations.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'button-list';
            townData.sub_locations.forEach(subLoc => {
                const li = document.createElement('li');
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'action-button sub-location-button';
                button.dataset.sublocName = subLoc.name;
                button.textContent = subLoc.name;
                li.appendChild(button);
                ul.appendChild(li);
            });
            DOM.subLocationsListDiv.appendChild(ul);
        } else {
            DOM.subLocationsListDiv.innerHTML = '<p>No sub-locations here.</p>';
        }
    },

    displaySubLocationActions(subLocName) {
        if (!DOM.currentSubLocationActionsListDiv || !DOM.currentSubLocationNameDisplay) return;
        DOM.currentSubLocationActionsListDiv.innerHTML = '';
        hideAllDynamicForms();

        currentSubLocationName = subLocName; // Update global state
        DOM.currentSubLocationNameDisplay.textContent = subLocName;
        DOM.currentSubLocationNameDisplay.style.display = 'block';

        const currentTownName = DOM.currentTownDisplayActions.textContent;
        const townData = gameConfigData.allTownsData[currentTownName];
        const selectedSubLocation = townData?.sub_locations?.find(sl => sl.name === subLocName);

        if (selectedSubLocation && selectedSubLocation.actions && selectedSubLocation.actions.length > 0) {
            const ul = document.createElement('ul');
            ul.className = 'button-list';
            selectedSubLocation.actions.forEach(actionStr => {
                const li = document.createElement('li');
                const button = document.createElement('button');
                button.type = 'button';
                button.className = 'action-button subloc-action-button';
                button.dataset.actionName = actionStr;
                button.textContent = actionStr.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
                li.appendChild(button);
                ul.appendChild(li);
            });
            DOM.currentSubLocationActionsListDiv.appendChild(ul);
        } else {
            DOM.currentSubLocationActionsListDiv.innerHTML = '<p>No actions available here.</p>';
        }
    },

    handleDirectActionSubmit(actionName, details = {}, buttonElement = null) {
        if (DOM.hiddenActionNameInput) DOM.hiddenActionNameInput.value = actionName;
        if (DOM.hiddenDetailsInput) DOM.hiddenDetailsInput.value = JSON.stringify(details);
        if (DOM.actionForm) {
            if (buttonElement) buttonElement.classList.add('button-processing');
            DOM.actionForm.submit();
        }
    },

    // More complex handler for actions that might open forms
    handleActionClick(actionName, buttonElement = null) {
        if (DOM.hiddenActionNameInput) DOM.hiddenActionNameInput.value = actionName;

        switch (actionName) {
            case CONSTANTS.ACTION_NAMES.CRAFT:
                showDynamicForm(DOM.craftDetailsDiv);
                break;
            case CONSTANTS.ACTION_NAMES.BUY_FROM_OWN_SHOP:
                showDynamicForm(DOM.buyDetailsDiv);
                break;
            case CONSTANTS.ACTION_NAMES.SELL_TO_OWN_SHOP:
                UIShopAndInventory.populateSellDropdown();
                showDynamicForm(DOM.sellDetailsDiv);
                break;
            case CONSTANTS.ACTION_NAMES.BUY_FROM_NPC:
                if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.HEMLOCK_HUT) {
                    this.populateNpcShopUI(CONSTANTS.NPC_NAMES.HEMLOCK);
                    showDynamicForm(DOM.hemlockHerbsDetailsDiv);
                } else if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.BORIN_SMITHY) {
                    this.populateNpcShopUI(CONSTANTS.NPC_NAMES.BORIN);
                    showDynamicForm(DOM.borinItemsDetailsDiv);
                }
                break;
            case CONSTANTS.ACTION_NAMES.TALK_TO_BORIN: // Assuming this might lead to buy options
                 if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.BORIN_SMITHY) {
                    this.populateNpcShopUI(CONSTANTS.NPC_NAMES.BORIN);
                    showDynamicForm(DOM.borinItemsDetailsDiv);
                }
                break;
            case CONSTANTS.ACTION_NAMES.REPAIR_GEAR_BORIN:
                if (currentSubLocationName === CONSTANTS.SUB_LOCATIONS.BORIN_SMITHY) {
                    this.populateBorinRepairUI();
                    showDynamicForm(DOM.borinRepairDetailsDiv);
                }
                break;
            // Direct submit actions:
            case CONSTANTS.ACTION_NAMES.GATHER_RESOURCES:
            case CONSTANTS.ACTION_NAMES.STUDY_LOCAL_HISTORY:
            case CONSTANTS.ACTION_NAMES.ORGANIZE_INVENTORY:
            case CONSTANTS.ACTION_NAMES.POST_ADVERTISEMENTS:
            case CONSTANTS.ACTION_NAMES.REST_SHORT:
            case CONSTANTS.ACTION_NAMES.REST_LONG:
                this.handleDirectActionSubmit(actionName, {}, buttonElement);
                break;
            default:
                console.warn(`Unhandled action: ${actionName}`);
                // Optionally submit with empty details if it's a generic action not listed
                // this.handleDirectActionSubmit(actionName, {}, buttonElement);
                break;
        }
    },

    populateNpcShopUI(npcName) {
        let targetListDiv, itemsData, selectedItemStateKey, itemNameField;
        if (npcName === CONSTANTS.NPC_NAMES.HEMLOCK) {
            targetListDiv = DOM.hemlockHerbsListDiv;
            itemsData = gameConfigData.hemlockHerbsData;
            selectedItemStateKey = 'selectedHemlockHerbName';
            itemNameField = 'herb-name';
        } else if (npcName === CONSTANTS.NPC_NAMES.BORIN) {
            targetListDiv = DOM.borinItemsListDiv;
            itemsData = gameConfigData.borinItemsData;
            selectedItemStateKey = 'selectedBorinItemName';
            itemNameField = 'item-name';
        } else {
            return;
        }

        window[selectedItemStateKey] = null; // Reset global state for selection, e.g., selectedHemlockHerbName = null;
        if (targetListDiv) {
            targetListDiv.innerHTML = '';
            if (itemsData && Object.keys(itemsData).length > 0) {
                const ul = document.createElement('ul');
                ul.className = 'npc-item-list'; // Add class for styling
                for (const itemKey in itemsData) {
                    const item = itemsData[itemKey];
                    const li = document.createElement('li');
                    // Using template literals for cleaner HTML string construction
                    li.innerHTML = `
                        <strong>${item.name}</strong> - ${item.price}G<br>
                        <em>${item.description}</em><br>
                        <button type="button" class="action-button select-npc-item-button" data-${itemNameField}="${item.name}" data-npc="${npcName}">Select</button>
                    `;
                    ul.appendChild(li);
                }
                targetListDiv.appendChild(ul);
            } else {
                targetListDiv.innerHTML = `<p>No items available from ${npcName}.</p>`;
            }
        }
    },

    populateBorinRepairUI() {
        if (DOM.borinRepairItemSelect) {
            DOM.borinRepairItemSelect.innerHTML = '<option value="">-- Select Item --</option>';
            if (gameConfigData.playerInventoryForSellDropdown && gameConfigData.playerInventoryForSellDropdown.length > 0) {
                gameConfigData.playerInventoryForSellDropdown.forEach(item => {
                    const itemName = (typeof item === 'string') ? item : item.name;
                    if (itemName) {
                        const option = document.createElement('option');
                        option.value = itemName;
                        option.textContent = itemName;
                        DOM.borinRepairItemSelect.appendChild(option);
                    }
                });
            } else {
                DOM.borinRepairItemSelect.innerHTML = '<option value="">-- No items to repair --</option>';
            }
            DOM.borinRepairItemSelect.onchange = function() {
                if (DOM.borinRepairCostDisplay) DOM.borinRepairCostDisplay.textContent = this.value ? "Cost determined by Borin" : "N/A";
            };
            if (DOM.borinRepairCostDisplay) DOM.borinRepairCostDisplay.textContent = "N/A";
        }
    },


    handleDynamicFormSubmit(event) {
        const targetButton = event.target.closest('.submit-details-button, #submit_buy_hemlock_herb_button, #submit_buy_borin_item_button, #submit-borin-repair-button');
        if (!targetButton) return;

        let details = {};
        let actionName = DOM.hiddenActionNameInput.value; // Should be set by handleActionClick

        if (currentOpenDynamicForm === DOM.craftDetailsDiv) {
            if (DOM.craftItemNameInput && DOM.craftItemNameInput.value) details.item_name = DOM.craftItemNameInput.value;
            actionName = CONSTANTS.ACTION_NAMES.CRAFT;
        } else if (currentOpenDynamicForm === DOM.buyDetailsDiv) {
            if (DOM.buyItemNameInput && DOM.buyItemNameInput.value) details.item_name = DOM.buyItemNameInput.value;
            if (DOM.buyQuantityInput && DOM.buyQuantityInput.value) details.quantity = parseInt(DOM.buyQuantityInput.value, 10);
            actionName = CONSTANTS.ACTION_NAMES.BUY_FROM_OWN_SHOP;
        } else if (currentOpenDynamicForm === DOM.sellDetailsDiv) {
            if (DOM.sellItemNameInput && DOM.sellItemNameInput.value) details.item_name = DOM.sellItemNameInput.value;
            actionName = CONSTANTS.ACTION_NAMES.SELL_TO_OWN_SHOP;
        } else if (currentOpenDynamicForm === DOM.hemlockHerbsDetailsDiv) {
            if (!selectedHemlockHerbName) { showToast("Please select an herb to buy.", "warning"); return; }
            const quantity = parseInt(DOM.hemlockQuantityInput.value, 10);
            if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity.", "warning"); return; }
            details = { npc_name: CONSTANTS.NPC_NAMES.HEMLOCK, item_name: selectedHemlockHerbName, quantity: quantity };
            actionName = CONSTANTS.ACTION_NAMES.BUY_FROM_NPC;
        } else if (currentOpenDynamicForm === DOM.borinItemsDetailsDiv) {
            if (!selectedBorinItemName) { showToast("Please select an item to buy from Borin.", "warning"); return; }
            const quantity = parseInt(DOM.borinQuantityInput.value, 10);
            if (isNaN(quantity) || quantity < 1) { showToast("Please enter a valid quantity.", "warning"); return; }
            details = { npc_name: CONSTANTS.NPC_NAMES.BORIN, item_name: selectedBorinItemName, quantity: quantity };
            actionName = CONSTANTS.ACTION_NAMES.BUY_FROM_NPC;
        } else if (currentOpenDynamicForm === DOM.borinRepairDetailsDiv) {
            const selectedItemToRepair = DOM.borinRepairItemSelect ? DOM.borinRepairItemSelect.value : null;
            if (!selectedItemToRepair) { showToast("Please select an item to repair.", "warning"); return; }
            details = { item_name_to_repair: selectedItemToRepair };
            actionName = CONSTANTS.ACTION_NAMES.REPAIR_GEAR_BORIN;
        }

        this.handleDirectActionSubmit(actionName, details, targetButton);
    },

    initEventListeners() {
        // Sub-location selection
        if (DOM.subLocationsListDiv) {
            DOM.subLocationsListDiv.addEventListener('click', (event) => {
                if (event.target.classList.contains('sub-location-button')) {
                    this.displaySubLocationActions(event.target.dataset.sublocName);
                }
            });
        }

        // Actions within a sub-location
        if (DOM.currentSubLocationActionsListDiv) {
            DOM.currentSubLocationActionsListDiv.addEventListener('click', (event) => {
                if (event.target.classList.contains('subloc-action-button')) {
                    this.handleActionClick(event.target.dataset.actionName, event.target);
                }
            });
        }

        // Map travel
        if (DOM.mapDestinationsDiv) {
            DOM.mapDestinationsDiv.addEventListener('click', (event) => {
                if (event.target.classList.contains('map-destination-button')) {
                    this.handleDirectActionSubmit(CONSTANTS.ACTION_NAMES.TRAVEL_TO_TOWN, { town_name: event.target.dataset.townName });
                }
            });
        }

        // General action buttons
        const generalActionButtons = [
            { el: DOM.gatherResourcesButton, name: CONSTANTS.ACTION_NAMES.GATHER_RESOURCES },
            { el: DOM.studyLocalHistoryButton, name: CONSTANTS.ACTION_NAMES.STUDY_LOCAL_HISTORY },
            { el: DOM.organizeInventoryButton, name: CONSTANTS.ACTION_NAMES.ORGANIZE_INVENTORY },
            { el: DOM.postAdvertisementsButton, name: CONSTANTS.ACTION_NAMES.POST_ADVERTISEMENTS },
            { el: DOM.shortRestButton, name: CONSTANTS.ACTION_NAMES.REST_SHORT },
            { el: DOM.longRestButton, name: CONSTANTS.ACTION_NAMES.REST_LONG },
        ];
        generalActionButtons.forEach(pair => {
            if (pair.el) {
                pair.el.addEventListener('click', () => this.handleActionClick(pair.name, pair.el));
            }
        });

        // NPC item selection (delegated)
        const handleNpcItemSelect = (event) => {
            const button = event.target.closest('.select-npc-item-button');
            if (!button) return;

            const npcName = button.dataset.npc;
            let selectedItemNameKey, listContainer;

            if (npcName === CONSTANTS.NPC_NAMES.HEMLOCK) {
                selectedHemlockHerbName = button.dataset.herbName;
                listContainer = DOM.hemlockHerbsListDiv;
            } else if (npcName === CONSTANTS.NPC_NAMES.BORIN) {
                selectedBorinItemName = button.dataset.itemName;
                listContainer = DOM.borinItemsListDiv;
            } else {
                return;
            }

            if (listContainer) {
                listContainer.querySelectorAll('.select-npc-item-button').forEach(btn => {
                    btn.style.fontWeight = 'normal'; btn.style.backgroundColor = ''; // Reset others
                    btn.classList.remove('selected-item-button'); // CSS class instead of inline style
                });
                button.style.fontWeight = 'bold'; // Or use a class:
                button.classList.add('selected-item-button');
            }
        };

        if (DOM.hemlockHerbsListDiv) DOM.hemlockHerbsListDiv.addEventListener('click', handleNpcItemSelect);
        if (DOM.borinItemsListDiv) DOM.borinItemsListDiv.addEventListener('click', handleNpcItemSelect);


        // Submit buttons in dynamic forms (delegated)
        if (DOM.dynamicActionFormsContainer) {
            DOM.dynamicActionFormsContainer.addEventListener('click', (event) => this.handleDynamicFormSubmit(event));
        }

        // Close buttons on dynamic forms
        if (DOM.closeDynamicFormButtons) {
            DOM.closeDynamicFormButtons.forEach(button => {
                button.addEventListener('click', () => {
                    hideAllDynamicForms();
                    if (DOM.currentTownDisplayActions && DOM.currentTownDisplayActions.textContent) {
                        this.displaySubLocations();
                    }
                });
            });
        }
    },

    init() {
        this.initEventListeners();
        // Initial population of sub-locations if town context exists
        if (DOM.currentTownDisplayActions && DOM.currentTownDisplayActions.textContent) {
            this.displaySubLocations();
        } else {
            if (DOM.subLocationsListDiv) DOM.subLocationsListDiv.innerHTML = '<p>No town context.</p>';
        }
    }
};


const UITopMenu = {
    init() {
        if (DOM.topRightMenuButton && DOM.settingsPopup) {
            DOM.topRightMenuButton.addEventListener('click', (event) => {
                event.stopPropagation();
                const isHidden = DOM.settingsPopup.style.display === 'none' || DOM.settingsPopup.style.display === '';
                DOM.settingsPopup.style.display = isHidden ? 'block' : 'none';
                DOM.topRightMenuButton.setAttribute('aria-expanded', isHidden.toString());
            });
        }

        if (DOM.saveGameButton) {
            DOM.saveGameButton.addEventListener('click', () => {
                showToast("Game progress is automatically saved after each action.", "info", 7000);
                if (DOM.settingsPopup) DOM.settingsPopup.style.display = 'none';
                if (DOM.topRightMenuButton) DOM.topRightMenuButton.setAttribute('aria-expanded', 'false');
            });
        }

        document.addEventListener('click', (event) => {
            if (DOM.settingsPopup && DOM.settingsPopup.style.display === 'block') {
                if (!DOM.settingsPopup.contains(event.target) && DOM.topRightMenuButton && !DOM.topRightMenuButton.contains(event.target)) {
                    DOM.settingsPopup.style.display = 'none';
                    if (DOM.topRightMenuButton) DOM.topRightMenuButton.setAttribute('aria-expanded', 'false');
                }
            }
        });
    }
};

const UIInitialPopups = {
    processEventPopup() {
        const { awaitingEventChoice, pendingEventDataJson } = gameConfigData;
        if (awaitingEventChoice && pendingEventDataJson && DOM.eventPopup) {
            try {
                const eventData = pendingEventDataJson; // Assuming it's already an object
                if (DOM.eventPopupNameEl) DOM.eventPopupNameEl.textContent = eventData.name || "An Event Occurs!";
                if (DOM.eventPopupDescriptionEl) DOM.eventPopupDescriptionEl.innerHTML = eventData.description || "You must make a choice.";

                if (DOM.eventPopupChoicesContainer) {
                    DOM.eventPopupChoicesContainer.innerHTML = ''; // Clear
                    if (eventData.choices && eventData.choices.length > 0) {
                        eventData.choices.forEach((choice, index) => {
                            const button = document.createElement('button');
                            button.className = 'event-choice-button action-button';
                            button.dataset.choiceIndex = index;
                            let buttonText = choice.text;
                            if (choice.skill && choice.dc) buttonText += ` <span class="skill-check-indicator">[${choice.skill} DC ${choice.dc}]</span>`;
                            if (choice.item_requirement_desc) buttonText += ` <span class="item-req-indicator">(${choice.item_requirement_desc})</span>`;
                            button.innerHTML = buttonText;
                            DOM.eventPopupChoicesContainer.appendChild(button);
                        });

                        // Event listener for choices (delegated, one-time attach)
                        if (!DOM.eventPopupChoicesContainer.dataset.listenerAttached) {
                            DOM.eventPopupChoicesContainer.addEventListener('click', (event) => {
                                if (event.target.classList.contains('event-choice-button')) {
                                    const choiceIndex = event.target.dataset.choiceIndex;
                                    const currentEventName = eventData.name; // Capture from closure

                                    if (choiceIndex === undefined || !currentEventName) {
                                        console.error("Error: Missing choice index or event name for event submission.");
                                        showToast("Error processing your choice.", "error");
                                        return;
                                    }
                                    // Submit choice via a dynamically created form
                                    const form = document.createElement('form');
                                    form.method = 'POST';
                                    form.action = gameConfigData.submitEventChoiceUrl;
                                    form.innerHTML = `
                                        <input type="hidden" name="event_name" value="${currentEventName}">
                                        <input type="hidden" name="choice_index" value="${choiceIndex}">
                                    `;
                                    document.body.appendChild(form);
                                    form.submit();
                                    if (DOM.eventPopup) DOM.eventPopup.style.display = 'none';
                                }
                            });
                            DOM.eventPopupChoicesContainer.dataset.listenerAttached = 'true';
                        }
                    } else {
                        DOM.eventPopupChoicesContainer.innerHTML = '<p>No choices available for this event.</p>';
                    }
                }
                if (DOM.eventPopup) DOM.eventPopup.style.display = 'block';
            } catch (e) {
                console.error("Error processing event data for popup:", e);
                if (DOM.eventPopup) DOM.eventPopup.style.display = 'none';
            }
        }
    },

    processActionResultToast() {
        const { popupActionResult } = gameConfigData;
        if (popupActionResult && popupActionResult.trim() !== "") {
            const toastMessage = popupActionResult.replace(/<br\s*\/?>/gi, " "); // Flatten <br>
            let actionResultType = 'info';
            const lowerMessage = toastMessage.toLowerCase();
            if (lowerMessage.includes('success')) actionResultType = 'success';
            else if (lowerMessage.includes('fail') || lowerMessage.includes('error') || lowerMessage.includes('not possible')) actionResultType = 'error';
            else if (lowerMessage.includes('warning')) actionResultType = 'warning';
            showToast(toastMessage, actionResultType, 7000);
        }
    },

    processSkillRollToast() {
        const { lastSkillRollStr } = gameConfigData;
        if (lastSkillRollStr && lastSkillRollStr.trim() !== "") {
            let skillRollType = 'info';
            const lowerMessage = lastSkillRollStr.toLowerCase();
            if (lowerMessage.includes('success')) skillRollType = 'success';
            else if (lowerMessage.includes('fail') || lowerMessage.includes('failure')) skillRollType = 'error';
            showToast(lastSkillRollStr, skillRollType, 7000);
        }
    },

    init() {
        this.processActionResultToast();
        this.processEventPopup();
        this.processSkillRollToast();
    }
};


// --- MAIN INITIALIZATION ---
function main() {
    document.body.classList.add('js-loaded');
    cacheDomElements(); // Populate DOM object
    loadConfigData(); // Populate gameConfigData object

    UIPanels.init();
    UIBottomTabs.init();
    UITopMenu.init();

    if (DOM.actionForm) { // Core game interactions are available
        UIActionsAndEvents.init();
        UIShopAndInventory.init();
    }

    UIInitialPopups.init();

    // Ensure all full panels are initially hidden after all JS setup
    if (DOM.fullPanelContainers) {
        DOM.fullPanelContainers.forEach(panel => {
            panel.classList.add('hidden');
            // Also ensure their corresponding mini-panels are not marked as expanded
            const miniPanel = document.querySelector(`[aria-controls="${panel.id}"]`);
            if (miniPanel) {
                miniPanel.setAttribute('aria-expanded', 'false');
            }
        });
    }
}

// --- STARTUP ---
document.addEventListener('DOMContentLoaded', main);
