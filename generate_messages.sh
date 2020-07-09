protoc \
	--plugin="protoc-gen-ts=${PROTOC_GEN_TS_PATH}" \
	--js_out=import_style=commonjs,binary:./nodejs/socketengine \
	--ts_out="./nodejs/socketengine" \
	--python_out="./python/socketengine" \
	message.proto

mv ./nodejs/socketengine/message_pb.js ./nodejs/socketengine/socketmessage.js 
mv ./nodejs/socketengine/message_pb.d.ts ./nodejs/socketengine/socketmessage.d.ts 
