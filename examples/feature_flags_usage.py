"""
Feature Flags Usage Examples

This file demonstrates how to use the new feature flags functionality
in the GroupPackage system for enabling/disabling additional features.

Example feature flags:
- "transaction_annotation": Enable transaction annotation features
- "daily_business_reports": Enable daily reports for business groups
- "advanced_analytics": Enable advanced analytics features
- "custom_export": Enable custom export formats
- "multi_currency": Enable multi-currency support
"""

from services.group_package_service import GroupPackageService

# Example usage functions
async def example_usage():
    """Example of how to use feature flags"""
    
    service = GroupPackageService()
    chat_id = 123456789  # Example chat ID
    
    # 1. Set individual feature flags
    print("Setting individual feature flags...")
    await service.set_feature_flag(chat_id, "transaction_annotation", True)
    await service.set_feature_flag(chat_id, "daily_business_reports", True)
    await service.set_feature_flag(chat_id, "advanced_analytics", False)
    
    # 2. Set multiple feature flags at once
    print("Setting multiple feature flags...")
    feature_flags = {
        "custom_export": True,
        "multi_currency": True,
        "premium_support": True
    }
    await service.update_feature_flags(chat_id, feature_flags)
    
    # 3. Check if features are enabled
    print("Checking feature flags...")
    has_annotation = await service.has_feature(chat_id, "transaction_annotation")
    has_reports = await service.get_feature_flag(chat_id, "daily_business_reports")
    has_analytics = await service.get_feature_flag(chat_id, "advanced_analytics", default=False)
    
    print(f"Transaction annotation: {has_annotation}")
    print(f"Daily business reports: {has_reports}")
    print(f"Advanced analytics: {has_analytics}")
    
    # 4. Get all feature flags
    print("Getting all feature flags...")
    all_flags = await service.get_all_feature_flags(chat_id)
    print(f"All feature flags: {all_flags}")
    
    # 5. Remove a feature flag
    print("Removing a feature flag...")
    await service.remove_feature_flag(chat_id, "advanced_analytics")
    
    # 6. Using feature flags in business logic
    print("Example business logic usage...")
    if await service.has_feature(chat_id, "transaction_annotation"):
        print("Show transaction annotation UI")
    else:
        print("Hide transaction annotation UI")
    
    if await service.has_feature(chat_id, "daily_business_reports"):
        print("Enable daily reports for business groups")
    else:
        print("Disable daily reports for business groups")


# Example integration in bot handlers
async def example_bot_integration():
    """Example of integrating feature flags in bot handlers"""
    
    service = GroupPackageService()
    
    async def handle_menu_command(chat_id: int):
        """Example menu handler with feature flags"""
        
        # Check if advanced features are enabled
        has_annotation = await service.has_feature(chat_id, "transaction_annotation")
        has_daily_reports = await service.has_feature(chat_id, "daily_business_reports")
        has_custom_export = await service.has_feature(chat_id, "custom_export")
        
        menu_options = ["📊 Basic Reports", "💰 View Balance"]
        
        if has_annotation:
            menu_options.append("📝 Add Transaction Notes")
        
        if has_daily_reports:
            menu_options.append("📅 Daily Business Reports")
        
        if has_custom_export:
            menu_options.append("📄 Custom Export")
        
        return menu_options
    
    async def handle_export_command(chat_id: int):
        """Example export handler with feature flags"""
        
        if not await service.has_feature(chat_id, "custom_export"):
            return "❌ Custom export feature is not enabled for your package"
        
        # Proceed with custom export logic
        return "✅ Custom export available"


# Example feature flag constants
class FeatureFlags:
    """Constants for feature flag keys"""
    
    TRANSACTION_ANNOTATION = "transaction_annotation"
    DAILY_BUSINESS_REPORTS = "daily_business_reports"
    ADVANCED_ANALYTICS = "advanced_analytics"
    CUSTOM_EXPORT = "custom_export"
    MULTI_CURRENCY = "multi_currency"
    PREMIUM_SUPPORT = "premium_support"
    SHIFT_MANAGEMENT = "shift_management"
    AUTOMATED_REPORTS = "automated_reports"
    API_ACCESS = "api_access"
    CUSTOM_BRANDING = "custom_branding"


# Example package-based feature defaults
async def setup_package_features(chat_id: int, package_type: str):
    """Setup default features based on package type"""
    
    service = GroupPackageService()
    
    if package_type == "TRIAL":
        features = {
            FeatureFlags.TRANSACTION_ANNOTATION: False,
            FeatureFlags.DAILY_BUSINESS_REPORTS: False,
            FeatureFlags.ADVANCED_ANALYTICS: False,
            FeatureFlags.CUSTOM_EXPORT: False,
        }
    elif package_type == "STANDARD":
        features = {
            FeatureFlags.TRANSACTION_ANNOTATION: True,
            FeatureFlags.DAILY_BUSINESS_REPORTS: True,
            FeatureFlags.ADVANCED_ANALYTICS: False,
            FeatureFlags.CUSTOM_EXPORT: False,
        }
    elif package_type == "BUSINESS":
        features = {
            FeatureFlags.TRANSACTION_ANNOTATION: True,
            FeatureFlags.DAILY_BUSINESS_REPORTS: True,
            FeatureFlags.ADVANCED_ANALYTICS: True,
            FeatureFlags.CUSTOM_EXPORT: True,
            FeatureFlags.SHIFT_MANAGEMENT: True,
            FeatureFlags.API_ACCESS: True,
        }
    else:
        features = {}
    
    await service.update_feature_flags(chat_id, features)
    print(f"Setup features for {package_type} package: {features}")


if __name__ == "__main__":
    import asyncio
    
    # Run examples
    asyncio.run(example_usage())
    asyncio.run(setup_package_features(123456789, "BUSINESS"))