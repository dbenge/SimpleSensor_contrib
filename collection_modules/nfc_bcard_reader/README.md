# NFC BCard Reader

Python3 SimpleSensor module to read NFC BCards provided by ITN using the Identiv SCL010 NFC reader.

## Messages
scan_in: { topic='scan_in', extended_data: {card_id: str} }


## Config variables
collection_point_type: Type (default `nfc_reader`)
collection_point_id: ID of collection point (default `nfc1`)
reader_port_number: Number of port to use as reader, should be 0 if you only have one NFC reader plugged in (default `0`)

See also: https://github.com/nfcpy/nfcpy