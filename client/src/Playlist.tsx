import React from "react";
import {changePlaylistTrackPosition, deleteTrackFromPlaylist, playlistChanged, PlaylistItem} from "./api";
import {createStyles, Theme, WithStyles, withStyles} from "@material-ui/core/styles";
import List from '@material-ui/core/List';
import {arrayMove, SortableContainer, SortableElement, SortEnd, SortEvent} from 'react-sortable-hoc';
import PlaylistEntry from "./PlaylistEntry";

interface PlaylistContextState {
    playlistItems: PlaylistItem[];
    playlistTrackUrls: ReadonlySet<string>;
    onSortEnd(sort: SortEnd, event: SortEvent): void;
    onDelete(playlistEntryId: string): void;
}

interface PlaylistContextProps {}

const INITIAL_CONTEXT_STATE: PlaylistContextState = { 
    playlistItems: [], 
    playlistTrackUrls: new Set(),
    onSortEnd(sort: SortEnd, event: SortEvent) { },
    onDelete(playlistEntryId: string) {},
};

const PlaylistContext = React.createContext<PlaylistContextState>(INITIAL_CONTEXT_STATE);


class PlaylistContextProvider extends React.Component<PlaylistContextProps, PlaylistContextState> {

    constructor(props: PlaylistContextProps) {
        super(props);
        this.state = INITIAL_CONTEXT_STATE;
    }

    componentDidMount() {
        playlistChanged(this.setPlaylist);
    }

    onSortEnd = (sort: SortEnd, event: SortEvent) => {
        const movedEntry = this.state.playlistItems[sort.oldIndex];
        const playlistItems = arrayMove(this.state.playlistItems, sort.oldIndex, sort.newIndex);
        this.setPlaylist(playlistItems);
        changePlaylistTrackPosition(movedEntry.playlist_entry_id, sort.newIndex)
    };

    onDelete = (playlistEntryId: string) => {
        const playlistItems = this.state.playlistItems.filter(item => item.playlist_entry_id !== playlistEntryId);
        this.setPlaylist(playlistItems);
        deleteTrackFromPlaylist(playlistEntryId);

    };

    setPlaylist = (items: PlaylistItem[]) => {
        this.setState({
            playlistItems: items,
            playlistTrackUrls: new Set(items.map(item => item.track.url)),
            onSortEnd: this.onSortEnd,
            onDelete: this.onDelete,
        });
    };

    render() {
        return (
            <PlaylistContext.Provider value={ {
                playlistItems: this.state.playlistItems,
                playlistTrackUrls: this.state.playlistTrackUrls,
                onSortEnd: this.state.onSortEnd,
                onDelete: this.state.onDelete,
            }}>
                {this.props.children}
            </PlaylistContext.Provider>
        );
    }
}

export {PlaylistContext, PlaylistContextProvider}

const styles = (theme: Theme) => createStyles({
    list: {
        overflow: 'auto'
    }
});

interface PlaylistState { }

interface PlaylistProps extends WithStyles<typeof styles> { }

const SortableItem = SortableElement(({playlistItem}: {playlistItem: PlaylistItem}) =>{
    return(
        <PlaylistEntry playlistItem={playlistItem} />
    );
});

const SortableList = SortableContainer(({playlistItems, classNames}: {playlistItems: PlaylistItem[], classNames: string}) => {
    return (

        <List dense className={classNames}>
            {playlistItems.map((value, index) => (
                <SortableItem key={`item-${index}`} index={index} playlistItem={value} />
            ))}
        </List>

    );
});

class Playlist extends React.Component<PlaylistProps, PlaylistState> {

    render() {
        const { classes } = this.props;

        return (
            <PlaylistContext.Consumer>
                {playlistContext => (
                <SortableList playlistItems={playlistContext.playlistItems}
                            classNames={classes.list}
                            onSortEnd={playlistContext.onSortEnd}
                            useDragHandle={true}
                            lockAxis={'y'} />
            )}
            </PlaylistContext.Consumer>
        );
    }
}
export default withStyles(styles) (Playlist);
