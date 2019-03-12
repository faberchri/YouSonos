import openSocket from 'socket.io-client';
import * as moment from 'moment';
import 'moment-duration-format';

let socket: any;
const albumIcon: string = require('../static/album_grey_192x192.png');

function initSocket() {
    let port = location.port;
    if (process.env.NODE_ENV !== 'production' && port === '3000') {
        // assume server is running on default port 5000 if we want to access the react dev server
        port = '5000';
    }
    const apiUrl = location.protocol + '//' + location.hostname + (port ? ':' + port : '');
    socket = openSocket(apiUrl);
}

export type TrackType =
    'youtube' |
    'null'

export type TrackStatus =
    'PLAYING' |
    'PAUSED' |
    'STOPPED'

export interface Track {
    title: string;
    artist: string;
    author: string;
    url: string;
    cover_url: string;
    track_type: TrackType;
    track_status: TrackStatus;
    duration: number;
}

const NULL_TRACK: Track = {
    title: '',
    artist: '',
    author: '',
    url: '',
    cover_url: albumIcon,
    track_type: 'null',
    track_status: "STOPPED",
    duration: 0,
};

export type PlaylistItemStatus =
    'WAITING' |
    'CURRENT' |
    'COMPLETED'

export interface PlaylistItem {
    playlist_entry_id: string;
    track: Track;
    status: PlaylistItemStatus
}

export interface Device {
    device_name: string;
    current_volume: number;
    max_volume: number;
}

export interface SearchResult {
    search_string: string;
    search_completed: boolean;
    has_error: boolean;
    results: Track[];
}

export type PlayerState =
    'PLAYING' |
    'PAUSED' |
    'STOPPED'

export interface CurrentPlayerState {
    player_state: PlayerState
}

type ReceiveEvent =
    'connect' |
    'sonos_setup' |
    'current_track' |
    'volume_changed' |
    'player_state' |
    'search_results' |
    'playlist_changed' |
    'player_time' |
    'player_time_update_activation'

function sonosSetup(callback: (devices: Device[]) => void) {
    receive('sonos_setup', callback);
}

function currentTrack(callback: (tracks: Track) => void) {
    receive('current_track', callback);
}

function volumeChanged(callback: (devices: Device[]) => void) {
    receive('volume_changed', callback);
}

function playerState(callback: (currentPlayerState: CurrentPlayerState) => void) {
    receive('player_state', callback);
}

function searchResults(callback: (searchResult: SearchResult) => void) {
    receive('search_results', callback)
}

function playlistChanged(callback: (tracks: PlaylistItem[]) => void) {
    receive('playlist_changed', callback)
}

function playerTime(callback: (time: number) => void) {
    receive('player_time', callback)
}

function playerTimeUpdateActivation(callback: (time: number) => void) {
    receive('player_time_update_activation', callback)
}

function receive(eventName: ReceiveEvent, callback: (arg: any) => void): void {
    socket.on(eventName, (payload: any) => {
        if (eventName !== 'player_time') {
            console.log('Calling Callback for received event', eventName, 'with payload', payload);
        }
        callback(payload);
    })
}

type SendEvent =
    'set_volume' |
    'toggle_play_pause' |
    'previous_track' |
    'next_track' |
    'search_tracks' |
    'cancel_search' |
    'play_track' |
    'add_track_to_playlist' |
    'delete_track_from_playlist' |
    'change_playlist_track_position' |
    'play_track_of_playlist' |
    'seek_to'

function setVolume(item: Device, new_volume: number) {
    emit('set_volume', {device_name: item.device_name, volume: new_volume})
}

function togglePlayPause() {
    emit('toggle_play_pause', {})
}

function playNextTrack() {
    emit('next_track', {})
}

function playPreviousTrack() {
    emit('previous_track', {})
}

function searchTracks(url: string) {
    emit('search_tracks', toYouTubeUrlJson(url))
}

function cancelSearch() {
    emit('cancel_search', {})
}

function playTrack(url: string) {
    emit('play_track', toYouTubeUrlJson(url))
}

function addTrackToPlaylist(url: string) {
    emit('add_track_to_playlist', toYouTubeUrlJson(url))
}

function deleteTrackFromPlaylist(playlistEntryId: string) {
    emit('delete_track_from_playlist', toPlaylistEntryIdJson(playlistEntryId))
}

function changePlaylistTrackPosition(playlistEntryId: string, target_position: number) {
    const payload = {playlist_entry_id: playlistEntryId, playlist_target_position: target_position};
    emit('change_playlist_track_position', payload)
}

function playTrackOfPlaylist(playlistEntryId: string) {
    emit('play_track_of_playlist', toPlaylistEntryIdJson(playlistEntryId))
}

function seekTo(timeInMilliseconds: number) {
    emit('seek_to', {player_time: timeInMilliseconds})
}

function toYouTubeUrlJson(url: string) {
    return {url: url}
}

function toYouTubeUrlWithPlaylistPositionJson(url: string, position: number) {
    return {url: url, playlist_position: position}
}

function toPlaylistEntryIdJson(playlistEntryId: string) {
    return {playlist_entry_id: playlistEntryId}
}

function emit(eventName: SendEvent, payload: any) {
    const json = JSON.stringify(payload);
    console.log('Emitting event', eventName, 'with payload', json);
    socket.emit(eventName, json );
}

function formatDuration(durationInMilliseconds: number): string {
    return moment.duration(durationInMilliseconds, 'milliseconds').format('h:*mm:ss');
}

export {
    initSocket,
    NULL_TRACK,
    sonosSetup,
    volumeChanged,
    setVolume,
    currentTrack,
    playerState,
    togglePlayPause,
    searchResults,
    searchTracks,
    cancelSearch,
    playTrack,
    playNextTrack,
    playPreviousTrack,
    playlistChanged,
    addTrackToPlaylist,
    playTrackOfPlaylist,
    deleteTrackFromPlaylist,
    changePlaylistTrackPosition,
    formatDuration,
    playerTime,
    playerTimeUpdateActivation,
    seekTo
}