protoc \
	--plugin="protoc-gen-ts=${PROTOC_GEN_TS_PATH}" \
	--js_out="./nodejs/socketengine" \
	--ts_out="./nodejs/socketengine" \
	--python_out="./python/socketengine" \
	message.proto
