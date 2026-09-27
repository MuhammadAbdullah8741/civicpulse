import http from 'k6/http';
import { check } from 'k6';
const rollout = __ENV.MODE === 'rollout';
const rate = Number(__ENV.RATE || 200);
const scenario = (startTime, duration, rate) => ({executor:'constant-arrival-rate',startTime,duration,rate,timeUnit:'1s',preAllocatedVUs:30,maxVUs:150,gracefulStop:'10s'});
export const options = {
  discardResponseBodies:true,
  scenarios: rollout ? {rollout:scenario('0s','180s',30)} : {
    baseline:scenario('0s','30s',5),
    load:scenario('30s','180s',rate),
  },
  thresholds:{http_req_failed:['rate==0'],checks:['rate==1'],dropped_iterations:['count==0']},
};
export default function () {
  const r = http.get('http://k3d-civicpulse-serverlb/api/complaints?page=1&page_size=100', {
    headers:{Host:'civicpulse.localhost'}, timeout:'10s',
  });
  check(r, {'HTTP 200':res=>res.status===200});
}
