export interface IPromise<TPromise> {
  resolve: (data?: TPromise) => void;
  reject: (error: Error) => void;
  promise: Promise<TPromise>;
}

export function DeferPromise<TPromise = void>(): IPromise<TPromise> {
  let resolve = (void 0 as unknown) as (data?: TPromise) => void;
  let reject = (void 0 as unknown) as (error: Error) => void;
  const promise = new Promise<TPromise>((_resolve, _reject) => {
    resolve = _resolve;
    reject = _reject;
  });

  return {
    resolve,
    reject,
    promise,
  };
}
