import rlp
from web3.auto import w3
from rlp.sedes import Binary, big_endian_int, binary

class ETHTransactionDecoder(object):
    class Transaction(rlp.Serializable):
        fields = [
            ("nonce", big_endian_int),
            ("gas_price", big_endian_int),
            ("gas", big_endian_int),
            ("to", Binary.fixed_length(20, allow_empty=True)),
            ("value", big_endian_int),
            ("data", binary),
            ("v", big_endian_int),
            ("r", big_endian_int),
            ("s", big_endian_int),
        ]

def DecodeRawTX(raw_tx):
    tx = rlp.decode(bytes.fromhex(raw_tx.replace("0x", "")), ETHTransactionDecoder.Transaction)
    from_ = w3.eth.account.recover_transaction(raw_tx)
    to = w3.toChecksumAddress(tx.to) if tx.to else None
    tokens = tx.value/1000000000000000000
    return from_, to, tokens