# SimpleSensor_contrib
## Repository for SimpleSensor's BTLE proximity module
What is a BTLE proximity module?  This SimpleSensor module uses BlueTooth scanning to locate Bluetooth beacons within a certian range of the scanning point.   

This was built and tuned for the BlueGiga bled112 device.  It has been used with other BTLE hardware devices as well. 

## Table of Contents

  * [Example Usage](#example-usage-types "Example usage")
  * [Configuration Settings](./BtleConfigSettings.md "BTLE Configuration settings")

### Example usage types

#### Example Proximity Gateway:  
- Person or thing wearing a bluetooth beacon is within 10m of scanner and event is thrown.    
- Then ever 3 seconds the beacon is seen within 10m a follow up event is thrown.  
- When the beacon has not been seen for 20 scans a exit event is thrown.

#### Example In gateway:
- Person or thing wearing a bluetooth beacon is within 10m of scanner and IN event is thrown.  
- No event is thrown when beason leaves the scan area

#### Example Out gateway:
- Person or thing wearing a bluetooth beacon is within 10m of scanner and OUT event is thrown
- No event is thrown when beason leaves the scan area

#### Example In/Out gateway:
- Person or thing wearing a bluetooth beacon is within 10m of scanner and IN event is thrown if its the first time we have seen the user
- After the beacon leaves the scan area then is seen again an OUT event is thrown

